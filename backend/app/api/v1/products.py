from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.product import Product
from app.schemas.supply_chain import ProductOut

router = APIRouter(prefix="/api/v1/products", tags=["products"])


@router.get("", response_model=list[ProductOut])
def list_products(category: str | None = None, db: Session = Depends(get_db), user=Depends(get_current_user)):
    q = db.query(Product)
    if category:
        q = q.filter(Product.category == category)
    return q.limit(500).all()
