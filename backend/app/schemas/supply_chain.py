from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class SupplierOut(BaseModel):
    id: str
    name: str
    location: Optional[str] = None
    country: Optional[str] = None
    reliability_score: float
    lead_time: int
    average_delay: float
    risk_level: str
    risk_score: float
    disruption_count: int

    class Config:
        from_attributes = True


class ProductOut(BaseModel):
    id: str
    sku: str
    name: str
    category: Optional[str] = None
    supplier_id: str
    unit_cost: float
    selling_price: float
    lead_time: int
    safety_stock: float
    reorder_point: float

    class Config:
        from_attributes = True


class InventoryOut(BaseModel):
    """
    Enriched inventory row: includes the product's SKU/name/category
    (joined server-side) so the frontend never has to display a bare,
    unreadable product UUID.
    """
    id: str
    product_id: str
    sku: Optional[str] = None
    product_name: Optional[str] = None
    category: Optional[str] = None
    current_stock: float
    reserved_stock: float
    available_stock: float
    reorder_point: float
    safety_stock: float
    last_updated: datetime

    class Config:
        from_attributes = True


class DisruptionEventOut(BaseModel):
    id: str
    disruption_type: Optional[str]
    severity: str
    location: Optional[str]
    affected_supplier: Optional[str]
    affected_product: Optional[str]
    confidence: float
    event_date: datetime
    description: Optional[str]

    class Config:
        from_attributes = True


class ForecastOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    product_id: str
    forecast_date: date
    predicted_demand: float
    lower_bound: Optional[float]
    upper_bound: Optional[float]
    model_version: str


class RecommendationOut(BaseModel):
    id: str
    product_id: str
    recommended_quantity: float
    recommended_order_date: Optional[date]
    reason: Optional[str]
    expected_cost: Optional[float]
    risk_reduction: Optional[float]

    class Config:
        from_attributes = True


class ScenarioRequest(BaseModel):
    product_id: str
    supplier_delay_days: int = 0
    demand_change_pct: float = 0.0
    transport_cost_change_pct: float = 0.0
    disruption_duration_days: int = 0


class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str
