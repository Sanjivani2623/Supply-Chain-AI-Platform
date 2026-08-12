"""
Event Registry API client.

Refactored from the original notebook (Infosys_Intern_Proj_Data.ipynb /
Product_based_Risk___Summarization.ipynb) into a reusable, configurable service.
Nothing here is hard-coded: API key, keywords, language, date range, and max
articles are all supplied by the caller / configuration.
"""
from datetime import date, timedelta
from typing import Optional

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

EVENT_REGISTRY_URL = "https://eventregistry.org/api/v1/article/getArticles"

DEFAULT_KEYWORDS = [
    "supply chain disruption",
    "logistics disruption",
    "shipping delay",
    "port congestion",
    "supplier disruption",
    "factory shutdown",
    "production delay",
    "raw material shortage",
    "semiconductor shortage",
    "transportation disruption",
    "freight disruption",
    "labor strike",
    "natural disaster supply chain",
]


class EventRegistryClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.EVENT_REGISTRY_API_KEY

    def fetch_articles(
        self,
        keywords: Optional[list[str]] = None,
        lang: str = "eng",
        days_back: int = 3,
        max_articles: int = 50,
        source: Optional[str] = None,
        country: Optional[str] = None,
    ) -> list[dict]:
        """Fetch raw articles for one or more keywords. Returns a de-duplicated list."""
        if not self.api_key:
            logger.warning("event_registry.no_api_key", msg="Falling back - no API key configured")
            return []

        keywords = keywords or DEFAULT_KEYWORDS
        date_end = date.today()
        date_start = date_end - timedelta(days=days_back)

        results: dict[str, dict] = {}
        with httpx.Client(timeout=30) as client:
            for kw in keywords:
                params = {
                    "apiKey": self.api_key,
                    "keyword": kw,
                    "count": max_articles,
                    "lang": lang,
                    "dateStart": date_start.isoformat(),
                    "dateEnd": date_end.isoformat(),
                    "articlesSortBy": "date",
                    "resultType": "articles",
                }
                if source:
                    params["sourceUri"] = source
                if country:
                    params["locationUri"] = country
                try:
                    resp = client.get(EVENT_REGISTRY_URL, params=params)
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as exc:  # network / API errors must not crash ingestion
                    logger.error("event_registry.fetch_failed", keyword=kw, error=str(exc))
                    continue

                articles = (data.get("articles", {}) or {}).get("results", [])
                for a in articles:
                    url = a.get("url")
                    if not url:
                        continue
                    results[url] = {
                        "title": a.get("title"),
                        "url": url,
                        "source": (a.get("source") or {}).get("title"),
                        "published_at": a.get("dateTimePub") or a.get("date"),
                        "content": a.get("body") or "",
                        "language": a.get("lang", lang),
                        "keyword": kw,
                    }
        return list(results.values())
