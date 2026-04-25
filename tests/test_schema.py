"""Tests for CANONICAL_HEADERS integrity."""

from gst_engine.schema import CANONICAL_HEADERS


def test_canonical_headers_count():
    assert len(CANONICAL_HEADERS) == 61, (
        f"Expected 61 canonical headers, got {len(CANONICAL_HEADERS)}"
    )


def test_no_duplicate_headers():
    dupes = [h for h in CANONICAL_HEADERS if CANONICAL_HEADERS.count(h) > 1]
    assert dupes == [], f"Duplicate canonical headers found: {set(dupes)}"


def test_no_empty_headers():
    empty = [h for h in CANONICAL_HEADERS if not h or not h.strip()]
    assert empty == [], "Empty or whitespace-only canonical headers found"
