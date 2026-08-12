from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.services.inventory.recommendation import generate_recommendation

router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])


@router.get("/{product_id}")
def get_recommendation(product_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return generate_recommendation(db, product_id)
