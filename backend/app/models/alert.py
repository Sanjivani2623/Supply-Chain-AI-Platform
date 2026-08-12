from sqlalchemy import Column, String, Text, DateTime
from datetime import datetime
from app.core.database import Base
from app.models.base import uuid_pk


class Alert(Base):
    __tablename__ = "alerts"

    id = uuid_pk()
    alert_type = Column(String, nullable=False)   # RISK/INVENTORY/SUPPLIER/DISRUPTION/DEMAND
    severity = Column(String, default="MEDIUM")
    title = Column(String, nullable=False)
    message = Column(Text)
    entity_type = Column(String)   # product/supplier/disruption
    entity_id = Column(String)
    status = Column(String, default="OPEN")  # OPEN/ACK/RESOLVED
    created_at = Column(DateTime, default=datetime.utcnow)
