from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.disruption_event import DisruptionEvent
from app.models.supplier import Supplier
from app.models.inventory import Inventory

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/kpis")
def kpis(db: Session = Depends(get_db), user=Depends(get_current_user)):
    active_disruptions = db.query(DisruptionEvent).count()
    high_risk_suppliers = db.query(Supplier).filter(Supplier.risk_level == "HIGH").count()
    inventory_at_risk = db.query(Inventory).filter(Inventory.available_stock < Inventory.reorder_point).count()
    return {
        "active_disruptions": active_disruptions,
        "high_risk_suppliers": high_risk_suppliers,
        "inventory_at_risk": inventory_at_risk,
    }


@router.get("/disruptions-by-type")
def disruptions_by_type(db: Session = Depends(get_db), user=Depends(get_current_user)):
    rows = db.query(DisruptionEvent.disruption_type, func.count(DisruptionEvent.id)).group_by(DisruptionEvent.disruption_type).all()
    return [{"type": t or "unknown", "count": c} for t, c in rows]


@router.get("/risk-by-country")
def risk_by_country(db: Session = Depends(get_db), user=Depends(get_current_user)):
    rows = db.query(Supplier.country, func.avg(Supplier.risk_score)).group_by(Supplier.country).all()
    return [{"country": c or "unknown", "avg_risk": round(float(r or 0), 1)} for c, r in rows]
