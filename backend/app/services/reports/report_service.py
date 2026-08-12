"""
Daily / weekly supply chain report generation (section 37).
"""
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.disruption_event import DisruptionEvent
from app.models.supplier import Supplier
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.inventory_recommendation import InventoryRecommendation


def generate_daily_report(db: Session) -> dict:
    since = datetime.utcnow() - timedelta(days=1)
    critical_disruptions = db.query(DisruptionEvent).filter(
        DisruptionEvent.event_date >= since, DisruptionEvent.severity.in_(["HIGH", "CRITICAL"])
    ).count()
    high_risk_suppliers = db.query(Supplier).filter(Supplier.risk_level == "HIGH").count()
    at_risk_products = db.query(Inventory).filter(Inventory.available_stock < Inventory.reorder_point).count()
    recent_recommendations = db.query(InventoryRecommendation).filter(
        InventoryRecommendation.created_at >= since
    ).count()

    top_event = db.query(DisruptionEvent).filter(DisruptionEvent.event_date >= since).order_by(
        DisruptionEvent.confidence.desc()
    ).first()

    return {
        "period": "daily",
        "generated_at": datetime.utcnow().isoformat(),
        "critical_disruptions": critical_disruptions,
        "high_risk_suppliers": high_risk_suppliers,
        "products_at_stockout_risk": at_risk_products,
        "recommended_orders": recent_recommendations,
        "top_risk": top_event.description if top_event else None,
    }


def generate_weekly_report(db: Session) -> dict:
    since = datetime.utcnow() - timedelta(days=7)
    disruptions = db.query(DisruptionEvent).filter(DisruptionEvent.event_date >= since).count()
    suppliers_ranked = db.query(Supplier).order_by(Supplier.risk_score.desc()).limit(5).all()
    return {
        "period": "weekly",
        "generated_at": datetime.utcnow().isoformat(),
        "total_disruptions": disruptions,
        "top_risk_suppliers": [{"name": s.name, "risk_score": s.risk_score} for s in suppliers_ranked],
    }
