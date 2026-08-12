"""
DocumentChunk stores RAG chunks + their embedding vector.

Embeddings are stored as a JSON-encoded list[float] in a Text column rather
than a native vector type, so this works identically on SQLite, Postgres,
MySQL, etc. with zero extensions required. Similarity search is done in
Python (see app/services/rag/retrieval.py) - fine at this project's scale
(hundreds-to-low-thousands of chunks); swap in a native vector column +
index if you outgrow that.
"""
from sqlalchemy import Column, String, Text, ForeignKey
from app.core.database import Base
from app.models.base import uuid_pk


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = uuid_pk()
    document_id = Column(String, ForeignKey("documents.id"), nullable=True, index=True)
    content = Column(Text, nullable=False)
    embedding = Column(Text)          # JSON-encoded list[float]
    chunk_metadata = Column(String)   # JSON-encoded metadata (source type, date, tags...)
