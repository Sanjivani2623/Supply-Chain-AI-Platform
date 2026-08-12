from sqlalchemy import Column, String, Text, DateTime
from datetime import datetime
from app.core.database import Base
from app.models.base import uuid_pk


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = uuid_pk()
    title = Column(String, nullable=False)
    url = Column(String, unique=True, nullable=False, index=True)
    url_hash = Column(String, unique=True, index=True)   # for idempotent dedup
    content_hash = Column(String, index=True)
    source = Column(String)
    published_at = Column(DateTime)
    content = Column(Text)
    summary = Column(Text)
    language = Column(String, default="eng")
    retrieved_at = Column(DateTime, default=datetime.utcnow)
