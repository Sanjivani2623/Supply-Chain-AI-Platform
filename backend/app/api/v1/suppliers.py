from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.supplier import Supplier
from app.schemas.supply_chain import SupplierOut

router = APIRouter(prefix="/api/v1/suppliers", tags=["suppliers"])


@router.get("", response_model=list[SupplierOut])
def list_suppliers(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(Supplier).order_by(Supplier.risk_score.desc()).all()


@router.get("/{supplier_id}", response_model=SupplierOut)
def get_supplier(supplier_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(Supplier).filter(Supplier.id == supplier_id).first()
