"""
Vector search + metadata filtering + (lightweight) reranking + grounded
context construction with citations (sections 20-21).

Similarity is computed in Python (cosine similarity over JSON-decoded
embeddings) rather than relying on a database-native vector index, so this
runs unmodified on SQLite as well as Postgres. Fine at this project's scale;
swap in pgvector + an ANN index if the document set grows large.
"""
import json

import numpy as np
from sqlalchemy.orm import Session

from app.models.document_chunk import DocumentChunk
from app.services.rag.embeddings import get_embedding_provider


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    a, b = np.array(a), np.array(b)
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def retrieve(db: Session, query: str, top_k: int = 5, source_filter: str | None = None) -> list[dict]:
    embedder = get_embedding_provider()
    query_vec = embedder.embed(query)

    rows = db.query(DocumentChunk).all()

    scored = []
    for row in rows:
        if not row.embedding:
            continue
        meta = {}
        try:
            meta = json.loads(row.chunk_metadata or "{}")
        except Exception:
            pass
        if source_filter and meta.get("source") != source_filter:
            continue
        try:
            vec = json.loads(row.embedding)
        except Exception:
            continue
        score = _cosine_similarity(query_vec, vec)
        scored.append((score, row, meta))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for score, row, meta in scored[:top_k]:
        results.append({
            "chunk_id": row.id,
            "document_id": row.document_id,
            "content": row.content,
            "metadata": meta,
            "score": round(score, 4),
        })
    return results


def build_context(chunks: list[dict]) -> tuple[str, list[dict]]:
    """Builds an LLM-ready context block + a parallel citations list."""
    context_lines = []
    citations = []
    for i, c in enumerate(chunks, start=1):
        label = c["metadata"].get("title") or c["metadata"].get("name") or f"Source {i}"
        context_lines.append(f"[{i}] {label}: {c['content'][:600]}")
        citations.append({"index": i, "label": label, "chunk_id": c["chunk_id"], "document_id": c["document_id"]})
    return "\n\n".join(context_lines), citations
