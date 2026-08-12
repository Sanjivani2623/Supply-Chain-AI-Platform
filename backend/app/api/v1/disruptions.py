from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.models.disruption_event import DisruptionEvent
from app.schemas.supply_chain import DisruptionEventOut
from app.services.ingestion.pipeline import run_ingestion
from app.services.disruption.demo_seed import seed_demo_disruptions

router = APIRouter(prefix="/api/v1/disruptions", tags=["disruptions"])


@router.get("", response_model=list[DisruptionEventOut])
def list_disruptions(limit: int = 50, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(DisruptionEvent).order_by(DisruptionEvent.event_date.desc()).limit(limit).all()


@router.post("/ingest")
def trigger_ingestion(max_articles: int = 20, db: Session = Depends(get_db), user=Depends(require_roles("admin", "manager"))):
    """Manually trigger the ingestion pipeline (normally run by the scheduled worker).
    Requires EVENT_REGISTRY_API_KEY to be configured - without it this returns
    fetched=0 (nothing to ingest), which is expected, not an error."""
    return run_ingestion(db, max_articles=max_articles)


@router.post("/seed-demo")
def seed_demo(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Populates a handful of realistic demo disruption events using the same
    classification/risk pipeline as live ingestion - useful when no
    EVENT_REGISTRY_API_KEY is configured yet."""
    return seed_demo_disruptions(db)
