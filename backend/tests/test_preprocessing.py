"""Unit tests for text preprocessing / dedup hashing used by the ingestion pipeline."""
from app.services.ingestion.preprocessing import clean_text, url_hash, content_hash, strip_html


def test_strip_html_removes_tags():
    assert strip_html("<p>Hello <b>world</b></p>") == " Hello  world  "


def test_clean_text_normalizes_whitespace():
    assert clean_text("Hello   \n\n world  ") == "Hello world"


def test_url_hash_is_deterministic_and_case_insensitive():
    a = url_hash("https://Example.com/Article")
    b = url_hash("https://example.com/article")
    assert a == b


def test_content_hash_changes_with_content():
    a = content_hash("Some article content about supply chains.")
    b = content_hash("Different content entirely.")
    assert a != b
