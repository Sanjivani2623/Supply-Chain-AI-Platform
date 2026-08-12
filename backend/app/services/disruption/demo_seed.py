"""
Seeds a handful of realistic disruption events for demo/local-dev purposes.

Without an EVENT_REGISTRY_API_KEY configured, the ingestion pipeline has
nothing to fetch, so the Disruptions page / dashboard charts stay empty by
design. This runs the *same* classification + risk-scoring pipeline the
real ingestion pipeline uses, just against a handful of canned article
texts instead of live news - so the demo experience is representative of
the real thing, not a hand-picked fake JSON blob.
"""
import random

from sqlalchemy.orm import Session

from app.models.news_article import NewsArticle
from app.models.disruption_event import DisruptionEvent
from app.models.supplier import Supplier
from app.services.disruption.classifier import classify_disruption
from app.services.disruption.risk_model import score_disruption_event
from app.services.ingestion.preprocessing import url_hash, content_hash

DEMO_ARTICLES = [
    ("Port congestion delays shipments out of major European hub",
     "Port congestion at a major European hub has caused significant shipping delay for "
     "containers, with transportation disruption expected to continue for several weeks "
     "as backlogs clear."),
    ("Factory shutdown hits automotive parts production",
     "A factory shutdown at a key automotive parts supplier has forced a production delay "
     "across several downstream manufacturers, with capacity reduction expected to persist "
     "into next quarter."),
    ("Semiconductor shortage continues to squeeze electronics makers",
     "The ongoing semiconductor shortage and broader raw material shortage are forcing "
     "electronics manufacturers to ration components, with some warning of further supplier "
     "disruption if the situation does not improve."),
    ("Labor strike disrupts freight movement",
     "A labor strike among dockworkers has led to freight disruption and shipping delay at "
     "several ports, compounding existing transportation disruption in the region."),
    ("Earthquake damages regional manufacturing capacity",
     "A natural disaster has damaged manufacturing capacity in an industrial region, causing "
     "factory shutdown at multiple plants and raising concern over supplier disruption for "
     "companies dependent on the area."),
    ("Trade tariffs raise costs for cross-border suppliers",
     "New tariffs and broader geopolitical tension are raising costs for suppliers moving "
     "goods across the affected border, with some businesses reporting early signs of "
     "raw material shortage as sourcing patterns shift."),
]


def seed_demo_disruptions(db: Session, count: int = 6) -> dict:
    suppliers = db.query(Supplier).all()
    created = 0

    for i, (title, text) in enumerate(DEMO_ARTICLES[:count]):
        fake_url = f"https://demo-news.local/article-{i}-{random.randint(1000,9999)}"
        uhash = url_hash(fake_url)
        if db.query(NewsArticle).filter(NewsArticle.url_hash == uhash).first():
            continue

        article = NewsArticle(
            title=title, url=fake_url, url_hash=uhash, content_hash=content_hash(text),
            source="Demo Seed", content=text, summary=text,
        )
        db.add(article)
        db.flush()

        classification = classify_disruption(text)
        if not classification["disruption_type"]:
            continue

        supplier = random.choice(suppliers) if suppliers else None
        event = DisruptionEvent(
            article_id=article.id,
            disruption_type=classification["disruption_type"],
            severity=classification["severity"],
            location=random.choice(["Rotterdam", "Shanghai", "Los Angeles", "Hamburg", "Singapore"]),
            affected_supplier=supplier.name if supplier else None,
            confidence=classification["confidence"],
            description=text,
        )
        db.add(event)
        db.flush()
        score_disruption_event(db, event)
        created += 1

    db.commit()
    return {"created": created}
