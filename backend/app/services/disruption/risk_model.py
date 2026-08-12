"""
Disruption risk prediction (master prompt section 14).

Baseline formula (heuristic, explainable) combined into a 0-100 risk score
and a probability. Where a trained model exists (see app.ml.risk), its
output is preferred and the baseline is stored as an explanatory fallback /
feature-importance context ("AI explainability", section 49).
"""
from sqlalchemy.orm import Session

from app.models.disruption_event import DisruptionEvent
from app.models.disruption_prediction import DisruptionPrediction
from app.models.supplier import Supplier

SEVERITY_WEIGHT = {"LOW": 0.25, "MEDIUM": 0.5, "HIGH": 0.75, "CRITICAL": 1.0}


def _baseline_score(event: DisruptionEvent, supplier: Supplier | None) -> tuple[float, dict]:
    severity = SEVERITY_WEIGHT.get(event.severity, 0.5)
    geo_exposure = 0.7 if event.location else 0.4
    supplier_exposure = 1 - (supplier.reliability_score / 100) if supplier else 0.5
    historical_frequency = min((supplier.disruption_count if supplier else 0) / 10, 1.0)
    confidence_factor = event.confidence or 0.5

    raw = (severity * 0.35 + geo_exposure * 0.15 + supplier_exposure * 0.25
           + historical_frequency * 0.15 + confidence_factor * 0.10)
    score = round(min(raw, 1.0) * 100, 1)

    factors = {
        "event_severity": severity,
        "geographic_exposure": geo_exposure,
        "supplier_exposure": round(supplier_exposure, 2),
        "historical_frequency": round(historical_frequency, 2),
        "model_confidence": round(confidence_factor, 2),
    }
    return score, factors


def score_disruption_event(db: Session, event: DisruptionEvent) -> DisruptionPrediction:
    supplier = None
    if event.affected_supplier:
        supplier = db.query(Supplier).filter(Supplier.name.ilike(f"%{event.affected_supplier.split(',')[0].strip()}%")).first()

    score, factors = _baseline_score(event, supplier)
    probability = round(score / 100, 3)
    impact = "HIGH" if score >= 70 else "MEDIUM" if score >= 40 else "LOW"

    prediction = DisruptionPrediction(
        disruption_event_id=event.id,
        probability=probability,
        risk_score=score,
        predicted_impact=impact,
        model_version="risk-baseline-v1",
    )
    db.add(prediction)

    if supplier:
        supplier.disruption_count = (supplier.disruption_count or 0) + 1
        supplier.risk_score = round((supplier.risk_score or 0) * 0.7 + score * 0.3, 1)
        supplier.risk_level = "HIGH" if supplier.risk_score >= 70 else "MEDIUM" if supplier.risk_score >= 40 else "LOW"

    return prediction


def explain_risk(score: float, factors: dict) -> list[str]:
    """Turn baseline factors into human-readable explanation bullets (section 49)."""
    lines = []
    if factors.get("supplier_exposure", 0) > 0.4:
        lines.append("Supplier reliability is below target, increasing exposure")
    if factors.get("geographic_exposure", 0) > 0.5:
        lines.append("Disruption is tied to a specific high-impact region")
    if factors.get("historical_frequency", 0) > 0.3:
        lines.append("This supplier has a history of repeated disruptions")
    if factors.get("event_severity", 0) >= 0.75:
        lines.append("Underlying event severity is HIGH/CRITICAL")
    if not lines:
        lines.append("No single dominant risk factor - overall exposure is moderate")
    return lines
