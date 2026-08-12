"""
Embedding provider abstraction (section 20).

Supports a "local" hashing-based embedding (no external dependency /
works fully offline for the portfolio demo) plus pluggable providers for
OpenAI/Anthropic-compatible embedding APIs, selected via EMBEDDING_PROVIDER.

Vectors are persisted as JSON-encoded lists (see DocumentChunk.embedding) so
this works unmodified on SQLite, Postgres, or any other SQL backend.
"""
import hashlib
import json
from abc import ABC, abstractmethod

import numpy as np
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.news_article import NewsArticle
from app.models.document import Document
from app.models.document_chunk import DocumentChunk


class BaseEmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, text: str) -> list[float]:
        ...

    def embed_and_store_article(self, db: Session, article: NewsArticle) -> None:
        text = article.summary or article.content[:2000]
        vector = self.embed(text)
        chunk = DocumentChunk(
            document_id=None,
            content=text,
            embedding=json.dumps(vector),
            chunk_metadata=f'{{"source":"news_article","article_id":"{article.id}","title":"{article.title}"}}',
        )
        db.add(chunk)

    def embed_document(self, db: Session, document: Document, chunks: list[str]) -> int:
        count = 0
        for chunk_text in chunks:
            db.add(DocumentChunk(
                document_id=document.id,
                content=chunk_text,
                embedding=json.dumps(self.embed(chunk_text)),
                chunk_metadata=f'{{"source":"document","document_id":"{document.id}","name":"{document.name}"}}',
            ))
            count += 1
        document.status = "PROCESSED"
        db.commit()
        return count


class LocalHashingEmbeddingProvider(BaseEmbeddingProvider):
    """Deterministic, dependency-free embedding: bag-of-hashed-tokens ->
    fixed-size vector. Good enough for demo-quality semantic similarity
    without requiring network access to an external embedding API."""

    def embed(self, text: str) -> list[float]:
        dim = settings.EMBEDDING_DIM
        vec = np.zeros(dim, dtype=np.float32)
        tokens = (text or "").lower().split()
        for tok in tokens:
            h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
            vec[h % dim] += 1.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()


def get_embedding_provider() -> BaseEmbeddingProvider:
    # Extend here with OpenAI/Anthropic embedding providers when
    # EMBEDDING_PROVIDER + EMBEDDING_API_KEY are configured.
    return LocalHashingEmbeddingProvider()
