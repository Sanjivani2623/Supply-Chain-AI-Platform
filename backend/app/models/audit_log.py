from sqlalchemy import Column, String, DateTime
from datetime import datetime
from app.core.database import Base
from app.models.base import uuid_pk


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = uuid_pk()
    user_id = Column(String, nullable=True)
    action = Column(String, nullable=False)
    entity = Column(String)
    entity_id = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
