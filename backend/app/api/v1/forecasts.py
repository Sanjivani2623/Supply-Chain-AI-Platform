from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.services.forecasting.forecast_service import generate_forecast

router = APIRouter(prefix="/api/v1/forecasts", tags=["forecasts"])


@router.get("/{product_id}")
def get_forecast(product_id: str, horizon: int = 14, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return generate_forecast(db, product_id, horizon=horizon)
