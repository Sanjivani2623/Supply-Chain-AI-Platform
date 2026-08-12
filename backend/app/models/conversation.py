from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from datetime import datetime
from app.core.database import Base
from app.models.base import uuid_pk


class Conversation(Base):
    __tablename__ = "conversations"

    id = uuid_pk()
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Message(Base):
    __tablename__ = "messages"

    id = uuid_pk()
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String, nullable=False)  # user | assistant | tool
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Citation(Base):
    __tablename__ = "citations"

    id = uuid_pk()
    message_id = Column(String, ForeignKey("messages.id"), nullable=False)
    document_id = Column(String, ForeignKey("documents.id"), nullable=True)
    chunk_id = Column(String, ForeignKey("document_chunks.id"), nullable=True)
    relevance_score = Column(String)
