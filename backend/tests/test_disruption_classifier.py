"""Unit tests for the keyword-baseline disruption classifier + severity + taxonomy."""
from app.services.disruption.classifier import classify_disruption, _keyword_classify, _severity


def test_classifies_shipping_delay():
    text = "Shipping delay reported at major port congestion in Rotterdam."
    result = classify_disruption(text)
    assert result["disruption_type"] in ("Logistics.Shipping Delay", "Logistics.Port Congestion")
    assert result["confidence"] > 0


def test_classifies_factory_shutdown_as_critical():
    text = "The company announced a full factory shutdown following the incident."
    result = classify_disruption(text)
    assert result["severity"] == "CRITICAL"


def test_no_match_returns_none():
    label, confidence = _keyword_classify("The weather today is sunny and pleasant.")
    assert label is None
    assert confidence == 0.0


def test_severity_defaults_to_low():
    assert _severity("Nothing unusual happened today.") == "LOW"
