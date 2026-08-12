from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.alert import Alert
from app.services.alerts.alert_engine import evaluate_inventory_below_reorder, evaluate_supplier_risk

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


@router.get("")
def list_alerts(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(Alert).order_by(Alert.created_at.desc()).limit(100).all()


@router.post("/run-checks")
def run_checks(db: Session = Depends(get_db), user=Depends(get_current_user)):
    inv_alerts = evaluate_inventory_below_reorder(db)
    supplier_alerts = evaluate_supplier_risk(db)
    return {"inventory_alerts": len(inv_alerts), "supplier_alerts": len(supplier_alerts)}
