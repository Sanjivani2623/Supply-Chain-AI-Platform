"""
Inventory recommendation engine (section 18) + What-If scenario simulator
(section 19). Combines forecast + inventory plan + supplier risk into a
concrete, explainable recommendation.
"""
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.inventory import Inventory
from app.models.supplier import Supplier
from app.models.inventory_recommendation import InventoryRecommendation
from app.services.forecasting.forecast_service import get_sales_series
from app.services.inventory.optimization import build_inventory_plan


def _demand_stats(series):
    if series.empty:
        return 0.0, 0.0, 0.0
    avg = float(series.mean())
    std = float(series.std() or 0.0)
    annual = float(series.sum()) * (365 / max(len(series), 1))
    return avg, std, annual


def generate_recommendation(db: Session, product_id: str) -> dict:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return {"error": "product_not_found"}
    inv = db.query(Inventory).filter(Inventory.product_id == product_id).first()
    supplier = db.query(Supplier).filter(Supplier.id == product.supplier_id).first()

    series = get_sales_series(db, product_id)
    avg_demand, demand_std, annual_demand = _demand_stats(series)
    current_stock = inv.available_stock if inv else 0.0
    disruption_risk = supplier.risk_score if supplier else 0.0

    plan = build_inventory_plan(
        avg_daily_demand=avg_demand,
        demand_std=demand_std,
        lead_time_days=product.lead_time,
        current_stock=current_stock,
        unit_cost=product.unit_cost,
        annual_demand=annual_demand,
        disruption_risk_score=disruption_risk,
    )

    order_qty = max(plan.reorder_point + plan.eoq - current_stock, 0)
    reasons = [f"Projected stockout probability is {plan.stockout_probability*100:.0f}%"]
    if supplier and supplier.risk_level in ("HIGH", "MEDIUM"):
        reasons.append(f"Supplier '{supplier.name}' risk level is {supplier.risk_level}")
    reasons.extend(plan.explanation)

    rec = None
    if order_qty > 0:
        rec = InventoryRecommendation(
            product_id=product_id,
            recommended_quantity=round(order_qty, 1),
            recommended_order_date=date.today() + timedelta(days=1 if plan.stockout_probability > 0.5 else 3),
            reason="; ".join(reasons),
            expected_cost=round(order_qty * product.unit_cost, 2),
            risk_reduction=round(min(plan.stockout_probability * 100, 100), 1),
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)

    return {
        "product_id": product_id,
        "sku": product.sku,
        "current_stock": current_stock,
        "safety_stock": plan.risk_adjusted_safety_stock,
        "reorder_point": plan.reorder_point,
        "eoq": plan.eoq,
        "stockout_probability": plan.stockout_probability,
        "recommended_quantity": round(order_qty, 1),
        "reason": "; ".join(reasons),
        "recommendation_id": rec.id if rec else None,
    }
