from sqlalchemy import Column, String, DateTime
from datetime import datetime
from app.core.database import Base
from app.models.base import uuid_pk


class User(Base):
    __tablename__ = "users"

    id = uuid_pk()
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="analyst")  # admin | manager | analyst
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
