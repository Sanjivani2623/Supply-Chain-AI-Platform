"""Unit tests for the disruption baseline risk scoring formula."""
from types import SimpleNamespace

from app.services.disruption.risk_model import _baseline_score, explain_risk


def _mock_event(severity="HIGH", location="Shanghai", confidence=0.8):
    return SimpleNamespace(severity=severity, location=location, confidence=confidence)


def _mock_supplier(reliability=50, disruption_count=5):
    return SimpleNamespace(reliability_score=reliability, disruption_count=disruption_count)


def test_higher_severity_increases_score():
    low = _baseline_score(_mock_event(severity="LOW"), _mock_supplier())
    high = _baseline_score(_mock_event(severity="CRITICAL"), _mock_supplier())
    assert high[0] > low[0]


def test_score_bounded_0_to_100():
    score, _ = _baseline_score(_mock_event(), _mock_supplier())
    assert 0 <= score <= 100


def test_explain_risk_returns_readable_bullets():
    score, factors = _baseline_score(_mock_event(severity="CRITICAL"), _mock_supplier(reliability=30, disruption_count=8))
    explanation = explain_risk(score, factors)
    assert isinstance(explanation, list)
    assert len(explanation) > 0
