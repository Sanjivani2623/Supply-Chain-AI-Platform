"""
Text preprocessing utilities: HTML removal, whitespace normalization,
sentence segmentation, language detection, dedup hashing.
"""
import hashlib
import re


HTML_TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")


def strip_html(text: str) -> str:
    return HTML_TAG_RE.sub(" ", text or "")


def normalize_whitespace(text: str) -> str:
    return WHITESPACE_RE.sub(" ", text or "").strip()


def clean_text(text: str) -> str:
    return normalize_whitespace(strip_html(text))


def url_hash(url: str) -> str:
    return hashlib.sha256(url.strip().lower().encode("utf-8")).hexdigest()


def content_hash(content: str) -> str:
    return hashlib.sha256(normalize_whitespace(content).encode("utf-8")).hexdigest()


def detect_language(text: str) -> str:
    """Very light heuristic language guess; defaults to English.
    A real deployment would use `langdetect` / `fasttext`."""
    if not text:
        return "eng"
    ascii_ratio = sum(1 for c in text if ord(c) < 128) / max(len(text), 1)
    return "eng" if ascii_ratio > 0.9 else "unknown"
