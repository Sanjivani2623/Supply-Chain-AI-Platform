from sqlalchemy import Column, Float, ForeignKey, DateTime, Text, String, Date
from datetime import datetime
from app.core.database import Base
from app.models.base import uuid_pk


class InventoryRecommendation(Base):
    __tablename__ = "inventory_recommendations"

    id = uuid_pk()
    product_id = Column(String, ForeignKey("products.id"), nullable=False, index=True)
    recommended_quantity = Column(Float, nullable=False)
    recommended_order_date = Column(Date)
    reason = Column(Text)
    expected_cost = Column(Float)
    risk_reduction = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
