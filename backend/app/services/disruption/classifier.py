"""
Disruption classification layer.

Implements the 3 approaches described in the master prompt (section 13):
1. Keyword baseline (fast, always available, refactor of original notebook logic)
2. ML classifier (TF-IDF + Logistic Regression, trained on labeled/synthetic data)
3. Optional LLM classification (used when confidence is low / for evaluation)

Callers should generally use `classify_disruption`, which uses (1) first and
can fall back to (2)/(3) when configured.
"""
from typing import Optional

from app.services.disruption.taxonomy import TAXONOMY, SEVERITY_KEYWORDS

_ml_model = None  # lazily loaded sklearn pipeline (see ml/classification/train.py)


def _keyword_classify(text: str) -> tuple[Optional[str], float]:
    text_l = (text or "").lower()
    best_type, best_hits = None, 0
    for label, keywords in TAXONOMY.items():
        hits = sum(1 for kw in keywords if kw in text_l)
        if hits > best_hits:
            best_type, best_hits = label, hits
    confidence = min(0.5 + 0.15 * best_hits, 0.95) if best_type else 0.0
    return best_type, confidence


def _severity(text: str) -> str:
    text_l = (text or "").lower()
    for level in ("CRITICAL", "HIGH", "MEDIUM"):
        if any(kw in text_l for kw in SEVERITY_KEYWORDS[level]):
            return level
    return "LOW"


def _ml_classify(text: str) -> Optional[tuple[str, float]]:
    global _ml_model
    if _ml_model is None:
        try:
            from app.ml.classification.model import load_model
            _ml_model = load_model()
        except Exception:
            _ml_model = False
    if not _ml_model:
        return None
    label, confidence = _ml_model.predict_one(text)
    return label, confidence


def classify_disruption(text: str, keyword_hint: Optional[str] = None) -> dict:
    kw_label, kw_conf = _keyword_classify(text)

    ml_result = _ml_classify(text)
    if ml_result and ml_result[1] > kw_conf:
        label, confidence, model_version = ml_result[0], ml_result[1], "tfidf-logreg-v1"
    else:
        label, confidence, model_version = kw_label, kw_conf, "keyword-baseline-v1"

    return {
        "disruption_type": label,
        "confidence": round(confidence, 3),
        "severity": _severity(text),
        "model_version": model_version,
    }
