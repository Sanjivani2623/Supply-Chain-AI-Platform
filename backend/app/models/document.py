from sqlalchemy import Column, String, DateTime, ForeignKey
from datetime import datetime
from app.core.database import Base
from app.models.base import uuid_pk


class Document(Base):
    __tablename__ = "documents"

    id = uuid_pk()
    name = Column(String, nullable=False)
    type = Column(String)          # pdf/docx/txt/csv
    source = Column(String)
    status = Column(String, default="PENDING")  # PENDING/PROCESSED/FAILED
    uploaded_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
