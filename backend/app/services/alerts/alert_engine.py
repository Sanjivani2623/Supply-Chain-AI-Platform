"""
Configurable alert rule evaluation (section 25).
"""
from sqlalchemy.orm import Session

from app.models.supplier import Supplier
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.disruption_prediction import DisruptionPrediction
from app.models.alert import Alert
from app.services.alerts.slack_service import send_slack_alert
from app.services.alerts.email_service import send_email_alert

DEFAULT_RULES = {
    "risk_score_threshold": 75,
    "stockout_probability_threshold": 0.6,
}


def _create_alert(db: Session, alert_type: str, severity: str, title: str, message: str, entity_type: str, entity_id: str) -> Alert:
    alert = Alert(alert_type=alert_type, severity=severity, title=title, message=message,
                  entity_type=entity_type, entity_id=entity_id)
    db.add(alert)
    db.commit()
    db.refresh(alert)
    send_slack_alert(f"🚨 {severity} - {title}\n{message}")
    send_email_alert(subject=title, body=message)
    return alert


def evaluate_disruption_risk(db: Session, prediction: DisruptionPrediction, threshold: float = DEFAULT_RULES["risk_score_threshold"]):
    if prediction.risk_score >= threshold:
        return _create_alert(
            db, "RISK", "HIGH" if prediction.risk_score < 90 else "CRITICAL",
            title=f"High disruption risk detected ({prediction.risk_score}/100)",
            message=f"Predicted impact: {prediction.predicted_impact}, probability: {prediction.probability}",
            entity_type="disruption_event", entity_id=prediction.disruption_event_id,
        )
    return None


def evaluate_inventory_below_reorder(db: Session):
    created = []
    rows = db.query(Inventory, Product).join(Product, Inventory.product_id == Product.id).filter(
        Inventory.available_stock < Inventory.reorder_point
    ).all()
    for inv, product in rows:
        created.append(_create_alert(
            db, "INVENTORY", "MEDIUM",
            title=f"{product.sku} below reorder point",
            message=f"Available stock {inv.available_stock} is below reorder point {inv.reorder_point}",
            entity_type="product", entity_id=product.id,
        ))
    return created


def evaluate_supplier_risk(db: Session):
    created = []
    for supplier in db.query(Supplier).filter(Supplier.risk_level == "HIGH").all():
        created.append(_create_alert(
            db, "SUPPLIER", "HIGH",
            title=f"Supplier '{supplier.name}' risk level is HIGH",
            message=f"Risk score {supplier.risk_score}/100, {supplier.disruption_count} historical disruptions",
            entity_type="supplier", entity_id=supplier.id,
        ))
    return created
