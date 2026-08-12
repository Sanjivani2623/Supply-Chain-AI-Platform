from fastapi import APIRouter

from app.api.v1 import (
    auth, suppliers, products, inventory, disruptions, forecasts,
    recommendations, scenarios, chat, documents, alerts, reports, analytics,
)

api_router = APIRouter()
for module in (auth, suppliers, products, inventory, disruptions, forecasts,
               recommendations, scenarios, chat, documents, alerts, reports, analytics):
    api_router.include_router(module.router)
