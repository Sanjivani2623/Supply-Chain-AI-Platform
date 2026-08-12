from sqlalchemy import Column, String, Float, Integer, DateTime
from datetime import datetime
from app.core.database import Base
from app.models.base import uuid_pk


class Supplier(Base):
    __tablename__ = "suppliers"

    id = uuid_pk()
    name = Column(String, nullable=False)
    location = Column(String)
    country = Column(String, index=True)
    reliability_score = Column(Float, default=80.0)   # 0-100
    lead_time = Column(Integer, default=7)             # days
    average_delay = Column(Float, default=0.0)          # days
    risk_level = Column(String, default="LOW")          # LOW/MEDIUM/HIGH
    risk_score = Column(Float, default=0.0)             # 0-100, computed
    disruption_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
