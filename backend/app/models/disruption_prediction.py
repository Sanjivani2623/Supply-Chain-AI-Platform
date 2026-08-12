from sqlalchemy import Column, Float, ForeignKey, DateTime, String
from datetime import datetime
from app.core.database import Base
from app.models.base import uuid_pk


class DisruptionPrediction(Base):
    __tablename__ = "disruption_predictions"

    id = uuid_pk()
    disruption_event_id = Column(String, ForeignKey("disruption_events.id"), nullable=False)
    probability = Column(Float, nullable=False)
    risk_score = Column(Float, nullable=False)
    predicted_impact = Column(String)   # LOW/MEDIUM/HIGH
    prediction_date = Column(DateTime, default=datetime.utcnow)
    model_version = Column(String, default="baseline-v1")
