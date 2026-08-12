from sqlalchemy import Column, Float, ForeignKey, Date, String
from app.core.database import Base
from app.models.base import uuid_pk


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = uuid_pk()
    supplier_id = Column(String, ForeignKey("suppliers.id"), nullable=False, index=True)
    product_id = Column(String, ForeignKey("products.id"), nullable=False, index=True)
    quantity = Column(Float, nullable=False)
    order_date = Column(Date, nullable=False)
    expected_date = Column(Date, nullable=False)
    actual_date = Column(Date, nullable=True)
    status = Column(String, default="PENDING")  # PENDING/DELIVERED/DELAYED/CANCELLED
