"""Structural validation for XLSL workbook data."""
from __future__ import annotations

from typing import Any
from .package import XLSLFormatError, _validate_workbook_shape


def validate_workbook(workbook: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    """Validate package structure, not domain types or execution semantics."""
    try:
        _validate_workbook_shape(workbook)
    except XLSLFormatError as exc:
        return False, {"valid": False, "errors": [str(exc)]}
    return True, {"valid": True, "errors": []}
