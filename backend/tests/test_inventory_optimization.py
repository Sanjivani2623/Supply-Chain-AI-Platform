"""Unit tests for inventory formulas (safety stock, reorder point, EOQ, stockout prob)."""
from app.services.inventory.optimization import (
    safety_stock, reorder_point, economic_order_quantity,
    stockout_probability, risk_adjusted_safety_stock, build_inventory_plan,
)


def test_safety_stock_increases_with_lead_time():
    low_lt = safety_stock(daily_demand_std=5, lead_time_days=3)
    high_lt = safety_stock(daily_demand_std=5, lead_time_days=15)
    assert high_lt > low_lt


def test_reorder_point_formula():
    rop = reorder_point(avg_daily_demand=10, lead_time_days=5, safety_stock_units=20)
    assert rop == 70.0  # 10*5 + 20


def test_eoq_positive():
    eoq = economic_order_quantity(annual_demand=3650, order_cost=50, holding_cost_per_unit=5)
    assert eoq > 0


def test_stockout_probability_bounds():
    p_safe = stockout_probability(current_stock=1000, expected_demand_during_lead_time=100, demand_std=10)
    p_risky = stockout_probability(current_stock=50, expected_demand_during_lead_time=200, demand_std=10)
    assert 0 <= p_safe <= 1
    assert 0 <= p_risky <= 1
    assert p_risky > p_safe


def test_risk_adjusted_safety_stock_scales_with_risk():
    low_risk, _ = risk_adjusted_safety_stock(100, disruption_risk_score=10)
    high_risk, _ = risk_adjusted_safety_stock(100, disruption_risk_score=85)
    assert high_risk > low_risk
    assert high_risk == 150.0  # 1.5x multiplier at HIGH risk


def test_build_inventory_plan_end_to_end():
    plan = build_inventory_plan(
        avg_daily_demand=20, demand_std=5, lead_time_days=10,
        current_stock=150, unit_cost=25, annual_demand=20 * 365,
        disruption_risk_score=80,
    )
    assert plan.safety_stock > 0
    assert plan.reorder_point > 0
    assert plan.eoq > 0
    assert 0 <= plan.stockout_probability <= 1
    assert plan.risk_adjusted_safety_stock > plan.safety_stock
