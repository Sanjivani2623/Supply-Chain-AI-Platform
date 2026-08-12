"""
Background task definitions (section 46). Each task opens its own DB
session so it can run independently of the request/response cycle.
"""
from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.services.ingestion.pipeline import run_ingestion
from app.services.forecasting.forecast_service import generate_forecast
from app.services.inventory.recommendation import generate_recommendation
from app.services.alerts.alert_engine import evaluate_inventory_below_reorder, evaluate_supplier_risk
from app.models.product import Product

logger = get_logger(__name__)


@celery_app.task(name="app.workers.tasks.ingest_news_task")
def ingest_news_task(max_articles: int = 50):
    db = SessionLocal()
    try:
        return run_ingestion(db, max_articles=max_articles)
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.daily_forecast_task")
def daily_forecast_task():
    db = SessionLocal()
    try:
        products = db.query(Product).all()
        results = []
        for p in products:
            forecast = generate_forecast(db, p.id, horizon=14)
            if "error" not in forecast:
                generate_recommendation(db, p.id)
            results.append(forecast)
        logger.info("daily_forecast_task.completed", products=len(results))
        return {"processed": len(results)}
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.run_alert_checks_task")
def run_alert_checks_task():
    db = SessionLocal()
    try:
        inv = evaluate_inventory_below_reorder(db)
        sup = evaluate_supplier_risk(db)
        return {"inventory_alerts": len(inv), "supplier_alerts": len(sup)}
    finally:
        db.close()
