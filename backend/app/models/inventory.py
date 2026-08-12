from sqlalchemy import Column, String, Float, ForeignKey, DateTime
from datetime import datetime
from app.core.database import Base
from app.models.base import uuid_pk


class Inventory(Base):
    __tablename__ = "inventory"

    id = uuid_pk()
    product_id = Column(String, ForeignKey("products.id"), nullable=False, index=True)
    current_stock = Column(Float, default=0.0)
    reserved_stock = Column(Float, default=0.0)
    available_stock = Column(Float, default=0.0)
    reorder_point = Column(Float, default=0.0)
    safety_stock = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=datetime.utcnow)
