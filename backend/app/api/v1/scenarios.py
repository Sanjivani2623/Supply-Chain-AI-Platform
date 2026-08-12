from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.supply_chain import ScenarioRequest
from app.services.inventory.scenario import run_scenario

router = APIRouter(prefix="/api/v1/scenarios", tags=["scenarios"])


@router.post("/simulate")
def simulate(payload: ScenarioRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return run_scenario(
        db, payload.product_id,
        supplier_delay_days=payload.supplier_delay_days,
        demand_change_pct=payload.demand_change_pct,
        transport_cost_change_pct=payload.transport_cost_change_pct,
        disruption_duration_days=payload.disruption_duration_days,
    )
