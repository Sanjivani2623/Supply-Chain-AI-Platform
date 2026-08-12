"""
What-if scenario simulator (section 19): supplier delay, demand shock,
transport cost changes, disruption duration.
"""
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.inventory import Inventory
from app.services.forecasting.forecast_service import get_sales_series
from app.services.inventory.optimization import build_inventory_plan


def run_scenario(
    db: Session,
    product_id: str,
    supplier_delay_days: int = 0,
    demand_change_pct: float = 0.0,
    transport_cost_change_pct: float = 0.0,
    disruption_duration_days: int = 0,
) -> dict:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return {"error": "product_not_found"}
    inv = db.query(Inventory).filter(Inventory.product_id == product_id).first()

    series = get_sales_series(db, product_id)
    if series.empty:
        return {"error": "insufficient_history"}

    avg_demand = float(series.mean()) * (1 + demand_change_pct / 100)
    demand_std = float(series.std() or 0.0) * (1 + abs(demand_change_pct) / 200)
    annual_demand = avg_demand * 365
    lead_time = product.lead_time + supplier_delay_days + (disruption_duration_days * 0.5)
    current_stock = inv.available_stock if inv else 0.0

    baseline = build_inventory_plan(
        avg_daily_demand=float(series.mean()),
        demand_std=float(series.std() or 0.0),
        lead_time_days=product.lead_time,
        current_stock=current_stock,
        unit_cost=product.unit_cost,
        annual_demand=float(series.mean()) * 365,
    )
    scenario = build_inventory_plan(
        avg_daily_demand=avg_demand,
        demand_std=demand_std,
        lead_time_days=lead_time,
        current_stock=current_stock,
        unit_cost=product.unit_cost * (1 + transport_cost_change_pct / 100),
        annual_demand=annual_demand,
    )

    additional_cost = round((scenario.eoq - baseline.eoq) * product.unit_cost * (1 + transport_cost_change_pct / 100), 2)
    service_level_before = round((1 - baseline.stockout_probability) * 100, 1)
    service_level_after = round((1 - scenario.stockout_probability) * 100, 1)

    return {
        "product_id": product_id,
        "inputs": {
            "supplier_delay_days": supplier_delay_days,
            "demand_change_pct": demand_change_pct,
            "transport_cost_change_pct": transport_cost_change_pct,
            "disruption_duration_days": disruption_duration_days,
        },
        "before": {
            "reorder_point": baseline.reorder_point,
            "safety_stock": baseline.safety_stock,
            "stockout_probability": baseline.stockout_probability,
            "service_level_pct": service_level_before,
        },
        "after": {
            "reorder_point": scenario.reorder_point,
            "safety_stock": scenario.safety_stock,
            "stockout_probability": scenario.stockout_probability,
            "service_level_pct": service_level_after,
            "required_reorder_quantity": scenario.eoq,
        },
        "additional_cost": additional_cost,
        "stockout_probability_delta": round(scenario.stockout_probability - baseline.stockout_probability, 3),
    }
