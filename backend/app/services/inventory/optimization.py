"""
Inventory optimization: safety stock, reorder point, EOQ, risk-adjusted
stock, and stockout probability (master prompt sections 17-18).
"""
import math
from dataclasses import dataclass

from scipy.stats import norm  # provided via scikit-learn deps chain; fallback below if missing


Z_SCORE_95 = 1.65  # service level ~95%


def _z_score(service_level: float) -> float:
    try:
        return float(norm.ppf(service_level))
    except Exception:
        return Z_SCORE_95


@dataclass
class InventoryPlan:
    safety_stock: float
    reorder_point: float
    eoq: float
    stockout_probability: float
    risk_adjusted_safety_stock: float
    explanation: list[str]


def safety_stock(daily_demand_std: float, lead_time_days: float, service_level: float = 0.95) -> float:
    z = _z_score(service_level)
    return round(z * daily_demand_std * math.sqrt(max(lead_time_days, 0.1)), 1)


def reorder_point(avg_daily_demand: float, lead_time_days: float, safety_stock_units: float) -> float:
    return round(avg_daily_demand * lead_time_days + safety_stock_units, 1)


def economic_order_quantity(annual_demand: float, order_cost: float, holding_cost_per_unit: float) -> float:
    if holding_cost_per_unit <= 0:
        return round(annual_demand / 12, 1)  # fallback: ~1 month of demand
    return round(math.sqrt((2 * annual_demand * order_cost) / holding_cost_per_unit), 1)


def stockout_probability(current_stock: float, expected_demand_during_lead_time: float, demand_std: float) -> float:
    if demand_std <= 0:
        return 0.0 if current_stock >= expected_demand_during_lead_time else 1.0
    z = (current_stock - expected_demand_during_lead_time) / demand_std
    try:
        prob_no_stockout = float(norm.cdf(z))
    except Exception:
        prob_no_stockout = 1 / (1 + math.exp(-z))  # logistic approx fallback
    return round(1 - prob_no_stockout, 3)


def risk_adjusted_safety_stock(base_safety_stock: float, disruption_risk_score: float) -> tuple[float, list[str]]:
    """If disruption probability increases, dynamically increase safety stock (section 17)."""
    explanation = []
    multiplier = 1.0
    if disruption_risk_score >= 70:
        multiplier = 1.5
        explanation.append(f"Disruption risk is HIGH ({disruption_risk_score}/100) - safety stock increased 50%")
    elif disruption_risk_score >= 40:
        multiplier = 1.2
        explanation.append(f"Disruption risk is MEDIUM ({disruption_risk_score}/100) - safety stock increased 20%")
    else:
        explanation.append(f"Disruption risk is LOW ({disruption_risk_score}/100) - no safety stock adjustment")
    return round(base_safety_stock * multiplier, 1), explanation


def build_inventory_plan(
    avg_daily_demand: float,
    demand_std: float,
    lead_time_days: float,
    current_stock: float,
    unit_cost: float,
    annual_demand: float,
    disruption_risk_score: float = 0.0,
    order_cost: float = 50.0,
    holding_cost_pct: float = 0.2,
    service_level: float = 0.95,
) -> InventoryPlan:
    ss = safety_stock(demand_std, lead_time_days, service_level)
    ras, explanation = risk_adjusted_safety_stock(ss, disruption_risk_score)
    rop = reorder_point(avg_daily_demand, lead_time_days, ras)
    eoq = economic_order_quantity(annual_demand, order_cost, unit_cost * holding_cost_pct)
    expected_demand_lt = avg_daily_demand * lead_time_days
    stockout_p = stockout_probability(current_stock, expected_demand_lt, demand_std * math.sqrt(max(lead_time_days, 0.1)))

    return InventoryPlan(
        safety_stock=ss,
        reorder_point=rop,
        eoq=eoq,
        stockout_probability=stockout_p,
        risk_adjusted_safety_stock=ras,
        explanation=explanation,
    )
