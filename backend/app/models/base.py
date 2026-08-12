import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, String


def gen_uuid():
    return str(uuid.uuid4())


class TimestampMixin:
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


def uuid_pk():
    # Stored as String (not Postgres UUID type) so it matches the String-typed
    # ForeignKey columns used throughout the model layer.
    return Column(String, primary_key=True, default=gen_uuid)
