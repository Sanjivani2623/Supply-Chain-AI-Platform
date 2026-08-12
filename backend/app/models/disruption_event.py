from sqlalchemy import Column, String, Float, ForeignKey, DateTime, Text
from datetime import datetime
from app.core.database import Base
from app.models.base import uuid_pk


class DisruptionEvent(Base):
    __tablename__ = "disruption_events"

    id = uuid_pk()
    article_id = Column(String, ForeignKey("news_articles.id"), nullable=True)
    disruption_type = Column(String, index=True)     # e.g. Logistics.Shipping Delay
    severity = Column(String, default="MEDIUM")       # LOW/MEDIUM/HIGH/CRITICAL
    location = Column(String)
    affected_supplier = Column(String, nullable=True)
    affected_product = Column(String, nullable=True)
    confidence = Column(Float, default=0.0)
    event_date = Column(DateTime, default=datetime.utcnow)
    description = Column(Text)
