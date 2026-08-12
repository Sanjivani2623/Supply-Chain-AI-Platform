from sqlalchemy import Column, Float, ForeignKey, Date, String
from app.core.database import Base
from app.models.base import uuid_pk


class Forecast(Base):
    __tablename__ = "forecasts"

    id = uuid_pk()
    product_id = Column(String, ForeignKey("products.id"), nullable=False, index=True)
    forecast_date = Column(Date, nullable=False)
    predicted_demand = Column(Float, nullable=False)
    lower_bound = Column(Float)
    upper_bound = Column(Float)
    model_version = Column(String, default="xgb-lag-v1")
