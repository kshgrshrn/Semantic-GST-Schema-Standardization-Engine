"""Core package for GST schema standardization."""
__version__ = "1.0.0"

from .schema import CANONICAL_HEADERS
from .mapper import SchemaMapper, ColumnResult, MappingResults

__all__ = ["__version__", "CANONICAL_HEADERS", "SchemaMapper", "ColumnResult", "MappingResults"]
