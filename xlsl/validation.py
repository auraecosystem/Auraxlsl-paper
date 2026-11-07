"""Versioned, typed validation for XLSL workbook structures."""
from __future__ import annotations
import json
import math
import re
from datetime import date, datetime
from typing import Any
from .package import XLSLFormatError, _validate_workbook_shape

SUPPORTED_SCHEMA_VERSION = 1
SUPPORTED_TYPES = {"string", "integer", "number", "boolean", "date", "datetime", "json"}
COLUMN_KEYS = {"name", "type", "nullable", "unique", "minimum", "maximum", "enum", "pattern"}


def _column_spec(column: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(column, str):
        return {"name": column, "type": None}
    if not isinstance(column, dict):
        raise XLSLFormatError("Column definitions must be strings or objects")
    unknown = set(column) - COLUMN_KEYS
    if unknown:
        raise XLSLFormatError(f"Unknown column properties: {sorted(unknown)}")
    name, kind = column.get("name"), column.get("type")
    if not isinstance(name, str) or not name:
        raise XLSLFormatError("Typed column definitions require a non-empty name")
    if kind not in SUPPORTED_TYPES:
        raise XLSLFormatError(f"Column {name!r} has unsupported type {kind!r}")
    for flag in ("nullable", "unique"):
        if flag in column and not isinstance(column[flag], bool):
            raise XLSLFormatError(f"Column {name!r} property {flag!r} must be boolean")
    if "enum" in column and not isinstance(column["enum"], list):
        raise XLSLFormatError(f"Column {name!r} enum must be an array")
    if "pattern" in column:
        if kind != "string" or not isinstance(column["pattern"], str):
            raise XLSLFormatError(f"Column {name!r} pattern requires a string column")
        try:
            re.compile(column["pattern"])
        except re.error as exc:
            raise XLSLFormatError(f"Column {name!r} has invalid regex pattern") from exc
    for bound in ("minimum", "maximum"):
        if bound in column and (kind not in {"integer", "number"} or
            isinstance(column[bound], bool) or not isinstance(column[bound], (int, float)) or
            not math.isfinite(column[bound])):
            raise XLSLFormatError(f"Column {name!r} {bound} requires a finite numeric type")
    if "minimum" in column and "maximum" in column and column["minimum"] > column["maximum"]:
        raise XLSLFormatError(f"Column {name!r} minimum exceeds maximum")
    return column


def _matches_type(value: Any, kind: str) -> bool:
    if kind == "string":
        return isinstance(value, str)
    if kind == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if kind == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    if kind == "boolean":
        return isinstance(value, bool)
    if kind == "date":
        if not isinstance(value, str):
            return False
        try:
            date.fromisoformat(value)
            return True
        except ValueError:
            return False
    if kind == "datetime":
        if not isinstance(value, str):
            return False
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
            return True
        except ValueError:
            return False
    if kind == "json":
        try:
            json.dumps(value, allow_nan=False)
            return True
        except (TypeError, ValueError):
            return False
    return False


def validate_workbook(workbook: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    """Validate shape, schema version, typed cells, and declarative constraints."""
    try:
        _validate_workbook_shape(workbook)
    except XLSLFormatError as exc:
        return False, {"valid": False, "errors": [str(exc)]}
    version = workbook.get("schema_version", 1)
    if not isinstance(version, int) or isinstance(version, bool) or version != SUPPORTED_SCHEMA_VERSION:
        return False, {"valid": False, "errors": [f"Unsupported workbook schema_version: {version!r}"]}

    errors: list[str] = []
    for sheet_name, sheet in workbook["sheets"].items():
        specs = [_column_spec(column) for column in sheet["columns"]]
        names = [spec["name"] for spec in specs]
        if len(set(names)) != len(names):
            errors.append(f"Sheet {sheet_name!r} has duplicate column names")
            continue
        unique_seen = {i: set() for i, spec in enumerate(specs) if spec.get("unique")}
        for row_number, row in enumerate(sheet["rows"], start=1):
            for index, (spec, value) in enumerate(zip(specs, row)):
                name, kind = spec["name"], spec.get("type")
                location = f"Sheet {sheet_name!r}, row {row_number}, column {name!r}"
                if value is None:
                    if kind and not spec.get("nullable", False):
                        errors.append(f"{location}: null is not allowed")
                    continue
                if kind and not _matches_type(value, kind):
                    errors.append(f"{location}: expected {kind}, got {type(value).__name__}")
                    continue
                if "enum" in spec and value not in spec["enum"]:
                    errors.append(f"{location}: value is not in the allowed enum")
                if "pattern" in spec and isinstance(value, str) and re.fullmatch(spec["pattern"], value) is None:
                    errors.append(f"{location}: value does not match pattern")
                if "minimum" in spec and value < spec["minimum"]:
                    errors.append(f"{location}: value is below minimum {spec['minimum']}")
                if "maximum" in spec and value > spec["maximum"]:
                    errors.append(f"{location}: value is above maximum {spec['maximum']}")
                if index in unique_seen:
                    marker = json.dumps(value, sort_keys=True, allow_nan=False)
                    if marker in unique_seen[index]:
                        errors.append(f"{location}: value violates unique constraint")
                    unique_seen[index].add(marker)
    return not errors, {"valid": not errors, "errors": errors}
