"""
Named entity recognition over article text.

Uses spaCy's small English model (as used in the original notebooks) to
extract companies/organizations, locations (countries, cities), and
generic entities relevant to supply-chain disruption analysis.
Falls back gracefully to a no-op extractor if the spaCy model isn't
installed in the current environment (keeps ingestion resilient).
"""
from typing import Optional

_nlp = None


def _get_nlp():
    global _nlp
    if _nlp is not None:
        return _nlp
    try:
        import spacy
        _nlp = spacy.load("en_core_web_sm")
    except Exception:
        _nlp = False  # sentinel: unavailable
    return _nlp


def extract_entities(text: str) -> dict:
    nlp = _get_nlp()
    result = {"organizations": [], "locations": [], "products": [], "gpe": []}
    if not nlp or not text:
        return result
    doc = nlp(text[:20000])  # cap for performance
    for ent in doc.ents:
        if ent.label_ == "ORG":
            result["organizations"].append(ent.text)
        elif ent.label_ in ("GPE", "LOC"):
            result["locations"].append(ent.text)
            result["gpe"].append(ent.text)
        elif ent.label_ == "PRODUCT":
            result["products"].append(ent.text)
    for k in result:
        result[k] = sorted(set(result[k]))
    return result
