"""
Agent tool implementations (section 23).

Every tool reads from the database / calls a real service function - the
LLM is never allowed to fabricate numbers (section 50). Each function's
docstring/signature is mirrored in TOOL_SPECS for the Anthropic tool-use
schema.
"""
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.supplier import Supplier
from app.models.inventory import Inventory
from app.models.disruption_event import DisruptionEvent
from app.models.disruption_prediction import DisruptionPrediction
from app.services.inventory.optimization import build_inventory_plan
from app.services.inventory.recommendation import generate_recommendation
from app.services.inventory.scenario import run_scenario
from app.services.forecasting.forecast_service import generate_forecast, get_sales_series
from app.services.rag.retrieval import retrieve, build_context


def get_current_inventory(db: Session, sku: str) -> dict:
    product = db.query(Product).filter(Product.sku == sku).first()
    if not product:
        return {"error": f"No product found with SKU {sku}"}
    inv = db.query(Inventory).filter(Inventory.product_id == product.id).first()
    if not inv:
        return {"error": "No inventory record found"}
    return {
        "sku": sku, "current_stock": inv.current_stock, "available_stock": inv.available_stock,
        "reorder_point": inv.reorder_point, "safety_stock": inv.safety_stock,
    }


def get_product_details(db: Session, sku: str) -> dict:
    product = db.query(Product).filter(Product.sku == sku).first()
    if not product:
        return {"error": f"No product found with SKU {sku}"}
    return {
        "sku": product.sku, "name": product.name, "category": product.category,
        "unit_cost": product.unit_cost, "selling_price": product.selling_price,
        "lead_time": product.lead_time, "supplier_id": product.supplier_id,
    }


def get_supplier_risk(db: Session, supplier_name: str) -> dict:
    supplier = db.query(Supplier).filter(Supplier.name.ilike(f"%{supplier_name}%")).first()
    if not supplier:
        return {"error": f"No supplier found matching '{supplier_name}'"}
    return {
        "name": supplier.name, "reliability_score": supplier.reliability_score,
        "average_delay": supplier.average_delay, "risk_level": supplier.risk_level,
        "risk_score": supplier.risk_score, "disruption_count": supplier.disruption_count,
    }


def get_disruption_events(db: Session, limit: int = 10) -> dict:
    events = db.query(DisruptionEvent).order_by(DisruptionEvent.event_date.desc()).limit(limit).all()
    return {"events": [
        {"id": e.id, "type": e.disruption_type, "severity": e.severity, "location": e.location,
         "affected_supplier": e.affected_supplier, "confidence": e.confidence, "date": str(e.event_date)}
        for e in events
    ]}


def get_risk_score(db: Session, disruption_event_id: str) -> dict:
    pred = db.query(DisruptionPrediction).filter(DisruptionPrediction.disruption_event_id == disruption_event_id).order_by(DisruptionPrediction.prediction_date.desc()).first()
    if not pred:
        return {"error": "No risk prediction found for this event"}
    return {"probability": pred.probability, "risk_score": pred.risk_score, "predicted_impact": pred.predicted_impact}


def get_demand_forecast(db: Session, sku: str, horizon: int = 14) -> dict:
    product = db.query(Product).filter(Product.sku == sku).first()
    if not product:
        return {"error": f"No product found with SKU {sku}"}
    return generate_forecast(db, product.id, horizon=horizon, persist=False)


def calculate_reorder_point(db: Session, sku: str) -> dict:
    product = db.query(Product).filter(Product.sku == sku).first()
    if not product:
        return {"error": f"No product found with SKU {sku}"}
    series = get_sales_series(db, product.id)
    if series.empty:
        return {"error": "insufficient_sales_history"}
    inv = db.query(Inventory).filter(Inventory.product_id == product.id).first()
    plan = build_inventory_plan(
        avg_daily_demand=float(series.mean()), demand_std=float(series.std() or 0),
        lead_time_days=product.lead_time, current_stock=inv.available_stock if inv else 0,
        unit_cost=product.unit_cost, annual_demand=float(series.mean()) * 365,
    )
    return {"sku": sku, "reorder_point": plan.reorder_point, "safety_stock": plan.safety_stock, "eoq": plan.eoq}


def calculate_safety_stock(db: Session, sku: str) -> dict:
    return calculate_reorder_point(db, sku)


def generate_inventory_recommendation(db: Session, sku: str) -> dict:
    product = db.query(Product).filter(Product.sku == sku).first()
    if not product:
        return {"error": f"No product found with SKU {sku}"}
    return generate_recommendation(db, product.id)


def simulate_supplier_delay(db: Session, sku: str, delay_days: int) -> dict:
    product = db.query(Product).filter(Product.sku == sku).first()
    if not product:
        return {"error": f"No product found with SKU {sku}"}
    return run_scenario(db, product.id, supplier_delay_days=delay_days)


def simulate_demand_change(db: Session, sku: str, demand_change_pct: float) -> dict:
    product = db.query(Product).filter(Product.sku == sku).first()
    if not product:
        return {"error": f"No product found with SKU {sku}"}
    return run_scenario(db, product.id, demand_change_pct=demand_change_pct)


def search_knowledge_base(db: Session, query: str) -> dict:
    chunks = retrieve(db, query, top_k=5, source_filter="document")
    context, citations = build_context(chunks)
    return {"context": context, "citations": citations}


def search_news(db: Session, query: str) -> dict:
    chunks = retrieve(db, query, top_k=5, source_filter="news_article")
    context, citations = build_context(chunks)
    return {"context": context, "citations": citations}


# ---- Tool registry: name -> callable(db, **kwargs) --------------------
TOOL_REGISTRY = {
    "get_current_inventory": get_current_inventory,
    "get_product_details": get_product_details,
    "get_supplier_risk": get_supplier_risk,
    "get_disruption_events": get_disruption_events,
    "get_risk_score": get_risk_score,
    "get_demand_forecast": get_demand_forecast,
    "calculate_reorder_point": calculate_reorder_point,
    "calculate_safety_stock": calculate_safety_stock,
    "generate_inventory_recommendation": generate_inventory_recommendation,
    "simulate_supplier_delay": simulate_supplier_delay,
    "simulate_demand_change": simulate_demand_change,
    "search_knowledge_base": search_knowledge_base,
    "search_news": search_news,
}

# Anthropic tool-use JSON schema for each tool.
TOOL_SPECS = [
    {"name": "get_current_inventory", "description": "Get current stock levels for a product by SKU.",
     "input_schema": {"type": "object", "properties": {"sku": {"type": "string"}}, "required": ["sku"]}},
    {"name": "get_product_details", "description": "Get product master data by SKU.",
     "input_schema": {"type": "object", "properties": {"sku": {"type": "string"}}, "required": ["sku"]}},
    {"name": "get_supplier_risk", "description": "Get a supplier's reliability and risk score by name.",
     "input_schema": {"type": "object", "properties": {"supplier_name": {"type": "string"}}, "required": ["supplier_name"]}},
    {"name": "get_disruption_events", "description": "List the most recent disruption events.",
     "input_schema": {"type": "object", "properties": {"limit": {"type": "integer"}}}},
    {"name": "get_risk_score", "description": "Get the risk prediction for a specific disruption event ID.",
     "input_schema": {"type": "object", "properties": {"disruption_event_id": {"type": "string"}}, "required": ["disruption_event_id"]}},
    {"name": "get_demand_forecast", "description": "Get demand forecast for a product by SKU.",
     "input_schema": {"type": "object", "properties": {"sku": {"type": "string"}, "horizon": {"type": "integer"}}, "required": ["sku"]}},
    {"name": "calculate_reorder_point", "description": "Calculate reorder point, safety stock and EOQ for a SKU.",
     "input_schema": {"type": "object", "properties": {"sku": {"type": "string"}}, "required": ["sku"]}},
    {"name": "calculate_safety_stock", "description": "Calculate safety stock for a SKU.",
     "input_schema": {"type": "object", "properties": {"sku": {"type": "string"}}, "required": ["sku"]}},
    {"name": "generate_inventory_recommendation", "description": "Generate an inventory reorder recommendation for a SKU.",
     "input_schema": {"type": "object", "properties": {"sku": {"type": "string"}}, "required": ["sku"]}},
    {"name": "simulate_supplier_delay", "description": "Simulate the impact of a supplier delay (in days) on a SKU.",
     "input_schema": {"type": "object", "properties": {"sku": {"type": "string"}, "delay_days": {"type": "integer"}}, "required": ["sku", "delay_days"]}},
    {"name": "simulate_demand_change", "description": "Simulate the impact of a demand change (percent) on a SKU.",
     "input_schema": {"type": "object", "properties": {"sku": {"type": "string"}, "demand_change_pct": {"type": "number"}}, "required": ["sku", "demand_change_pct"]}},
    {"name": "search_knowledge_base", "description": "Semantic search over uploaded internal documents (policies, SOPs, contracts).",
     "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
    {"name": "search_news", "description": "Semantic search over ingested news articles / disruption reports.",
     "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
]
