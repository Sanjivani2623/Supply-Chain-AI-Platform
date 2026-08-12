from sqlalchemy import Column, String, Float, ForeignKey, Date
from app.core.database import Base
from app.models.base import uuid_pk


class Sale(Base):
    __tablename__ = "sales"

    id = uuid_pk()
    product_id = Column(String, ForeignKey("products.id"), nullable=False, index=True)
    quantity = Column(Float, nullable=False)
    revenue = Column(Float, nullable=False)
    sale_date = Column(Date, nullable=False, index=True)
