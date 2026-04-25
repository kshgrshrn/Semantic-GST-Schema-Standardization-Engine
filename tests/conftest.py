"""Shared fixtures for GST engine tests."""

from __future__ import annotations

import pytest

from gst_engine.mapper import SchemaMapper


@pytest.fixture(scope="session")
def mapper() -> SchemaMapper:
    """A mapper instance shared across all tests (model load is expensive)."""
    return SchemaMapper(model_name="all-MiniLM-L6-v2", threshold=0.5)
