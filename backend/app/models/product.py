from sqlalchemy import Column, String, Float, Integer, ForeignKey
from app.core.database import Base
from app.models.base import uuid_pk


class Product(Base):
    __tablename__ = "products"

    id = uuid_pk()
    sku = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    category = Column(String, index=True)
    supplier_id = Column(String, ForeignKey("suppliers.id"), nullable=False)
    unit_cost = Column(Float, default=0.0)
    selling_price = Column(Float, default=0.0)
    lead_time = Column(Integer, default=7)
    safety_stock = Column(Float, default=0.0)
    reorder_point = Column(Float, default=0.0)
