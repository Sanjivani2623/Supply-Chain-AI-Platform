"""
Celery application + beat schedule (section 46).
"""
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery("supplychain_ai", broker=settings.REDIS_URL, backend=settings.REDIS_URL)

celery_app.conf.beat_schedule = {
    "ingest-news-every-6-hours": {
        "task": "app.workers.tasks.ingest_news_task",
        "schedule": crontab(minute=0, hour="*/6"),
    },
    "daily-forecast-and-recommendations": {
        "task": "app.workers.tasks.daily_forecast_task",
        "schedule": crontab(minute=0, hour=2),
    },
    "run-alert-checks-hourly": {
        "task": "app.workers.tasks.run_alert_checks_task",
        "schedule": crontab(minute=15, hour="*"),
    },
}
celery_app.conf.timezone = "UTC"
