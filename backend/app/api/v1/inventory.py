from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.inventory import Inventory
from app.models.product import Product
from app.schemas.supply_chain import InventoryOut

router = APIRouter(prefix="/api/v1/inventory", tags=["inventory"])


def _to_inventory_out(inv: Inventory, product: Product | None) -> InventoryOut:
    return InventoryOut(
        id=inv.id,
        product_id=inv.product_id,
        sku=product.sku if product else None,
        product_name=product.name if product else None,
        category=product.category if product else None,
        current_stock=inv.current_stock,
        reserved_stock=inv.reserved_stock,
        available_stock=inv.available_stock,
        reorder_point=inv.reorder_point,
        safety_stock=inv.safety_stock,
        last_updated=inv.last_updated,
    )


@router.get("", response_model=list[InventoryOut])
def list_inventory(db: Session = Depends(get_db), user=Depends(get_current_user)):
    rows = db.query(Inventory, Product).join(Product, Inventory.product_id == Product.id).limit(500).all()
    return [_to_inventory_out(inv, product) for inv, product in rows]


@router.get("/at-risk", response_model=list[InventoryOut])
def at_risk_inventory(db: Session = Depends(get_db), user=Depends(get_current_user)):
    rows = (
        db.query(Inventory, Product)
        .join(Product, Inventory.product_id == Product.id)
        .filter(Inventory.available_stock < Inventory.reorder_point)
        .all()
    )
    return [_to_inventory_out(inv, product) for inv, product in rows]
