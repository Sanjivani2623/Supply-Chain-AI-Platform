"""
End-to-end ingestion pipeline (idempotent).

News/API -> fetch -> validate -> dedup -> normalize -> store raw article
-> clean -> extract metadata -> summarize -> classify -> create disruption
event -> generate embeddings -> store vector -> trigger risk analysis.

This is the orchestration layer that replaces the old "notebook -> CSV"
flow with database-backed, idempotent processing.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.news_article import NewsArticle
from app.models.disruption_event import DisruptionEvent
from app.services.ingestion.event_registry_client import EventRegistryClient
from app.services.ingestion.preprocessing import clean_text, url_hash, content_hash
from app.services.ingestion.summarization import get_summarizer
from app.services.ingestion.entity_extraction import extract_entities
from app.services.disruption.classifier import classify_disruption
from app.services.rag.embeddings import get_embedding_provider
from app.services.disruption.risk_model import score_disruption_event

logger = get_logger(__name__)


def run_ingestion(
    db: Session,
    keywords: Optional[list[str]] = None,
    max_articles: int = 50,
    days_back: int = 3,
) -> dict:
    client = EventRegistryClient()
    raw_articles = client.fetch_articles(keywords=keywords, max_articles=max_articles, days_back=days_back)

    created, skipped, events_created = 0, 0, 0
    summarizer = get_summarizer("textrank")
    embedder = get_embedding_provider()

    for raw in raw_articles:
        uhash = url_hash(raw["url"])
        existing = db.query(NewsArticle).filter(NewsArticle.url_hash == uhash).first()
        if existing:
            skipped += 1
            continue

        content = clean_text(raw.get("content", ""))
        chash = content_hash(content)
        dup_content = db.query(NewsArticle).filter(NewsArticle.content_hash == chash).first()
        if dup_content:
            skipped += 1
            continue

        summary = summarizer.summarize(content, num_sentences=3)
        entities = extract_entities(content)

        published_at = None
        try:
            published_at = datetime.fromisoformat(str(raw.get("published_at")).replace("Z", "+00:00"))
        except Exception:
            published_at = datetime.utcnow()

        article = NewsArticle(
            title=raw.get("title") or "(untitled)",
            url=raw["url"],
            url_hash=uhash,
            content_hash=chash,
            source=raw.get("source"),
            published_at=published_at,
            content=content,
            summary=summary,
            language=raw.get("language", "eng"),
        )
        db.add(article)
        db.flush()  # get article.id
        created += 1

        classification = classify_disruption(content, keyword_hint=raw.get("keyword"))
        if classification["disruption_type"]:
            event = DisruptionEvent(
                article_id=article.id,
                disruption_type=classification["disruption_type"],
                severity=classification["severity"],
                location=", ".join(entities["locations"][:3]) or None,
                affected_supplier=", ".join(entities["organizations"][:3]) or None,
                affected_product=None,
                confidence=classification["confidence"],
                event_date=published_at,
                description=summary,
            )
            db.add(event)
            db.flush()
            events_created += 1

            # risk scoring for the newly created event
            score_disruption_event(db, event)

            # embeddings for RAG (index article summary as a retrievable chunk)
            try:
                embedder.embed_and_store_article(db, article)
            except Exception as exc:
                logger.warning("ingestion.embedding_failed", article_id=article.id, error=str(exc))

    db.commit()
    logger.info("ingestion.completed", created=created, skipped=skipped, events=events_created)
    return {"fetched": len(raw_articles), "created": created, "skipped": skipped, "disruption_events": events_created}
