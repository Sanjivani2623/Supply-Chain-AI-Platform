from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.services.reports.report_service import generate_daily_report, generate_weekly_report

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.get("/daily")
def daily_report(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return generate_daily_report(db)


@router.get("/weekly")
def weekly_report(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return generate_weekly_report(db)
