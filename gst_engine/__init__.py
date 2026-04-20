"""Core package for GST schema standardization."""

from .schema import CANONICAL_HEADERS
from .mapper import SchemaMapper

__all__ = ["CANONICAL_HEADERS", "SchemaMapper"]
