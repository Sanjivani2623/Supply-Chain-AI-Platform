export interface Supplier {
  id: string;
  name: string;
  location?: string;
  country?: string;
  reliability_score: number;
  lead_time: number;
  average_delay: number;
  risk_level: "LOW" | "MEDIUM" | "HIGH";
  risk_score: number;
  disruption_count: number;
}

export interface Product {
  id: string;
  sku: string;
  name: string;
  category?: string;
  supplier_id: string;
  unit_cost: number;
  selling_price: number;
  lead_time: number;
  safety_stock: number;
  reorder_point: number;
}

export interface InventoryItem {
  id: string;
  product_id: string;
  sku?: string;
  product_name?: string;
  category?: string;
  current_stock: number;
  reserved_stock: number;
  available_stock: number;
  reorder_point: number;
  safety_stock: number;
  last_updated: string;
}

export interface DisruptionEvent {
  id: string;
  disruption_type?: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  location?: string;
  affected_supplier?: string;
  affected_product?: string;
  confidence: number;
  event_date: string;
  description?: string;
}

export interface KPIs {
  active_disruptions: number;
  high_risk_suppliers: number;
  inventory_at_risk: number;
}
