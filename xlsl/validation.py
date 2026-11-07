"""Versioned, typed and relational validation for XLSL workbooks."""
from __future__ import annotations

import json
import math
import re
from datetime import date, datetime
from typing import Any

from .package import XLSLFormatError, _validate_workbook_shape

SUPPORTED_SCHEMA_VERSIONS = {1, 2}
SUPPORTED_TYPES = {"string", "integer", "number", "boolean", "date", "datetime", "json"}
COLUMN_KEYS = {"name", "type", "nullable", "unique", "minimum", "maximum", "enum", "pattern"}
DELETE_POLICIES = {"restrict", "cascade", "set_null"}


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
    if not isinstance(kind, str) or kind not in SUPPORTED_TYPES:
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
        if bound in column and (
            kind not in {"integer", "number"}
            or isinstance(column[bound], bool)
            or not isinstance(column[bound], (int, float))
            or not math.isfinite(column[bound])
        ):
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


def _key_spec(value: Any, label: str, errors: list[str]) -> list[str] | None:
    if not isinstance(value, list) or not value or any(not isinstance(v, str) or not v for v in value):
        errors.append(f"{label} must be a non-empty array of column names")
        return None
    if len(set(value)) != len(value):
        errors.append(f"{label} contains duplicate column names")
        return None
    return value


def validate_workbook(workbook: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    """Validate workbook shape, typed cells, keys, and cross-sheet references."""
    try:
        _validate_workbook_shape(workbook)
    except XLSLFormatError as exc:
        return False, {"valid": False, "errors": [str(exc)]}

    version = workbook.get("schema_version", 1)
    if not isinstance(version, int) or isinstance(version, bool) or version not in SUPPORTED_SCHEMA_VERSIONS:
        return False, {"valid": False, "errors": [f"Unsupported workbook schema_version: {version!r}"]}

    errors: list[str] = []
    sheets = workbook["sheets"]
    specs_by_sheet: dict[str, list[dict[str, Any]]] = {}
    indexes: dict[str, dict[str, int]] = {}

    for sheet_name, sheet in sheets.items():
        try:
            specs = [_column_spec(column) for column in sheet["columns"]]
        except XLSLFormatError as exc:
            errors.append(f"Sheet {sheet_name!r}: {exc}")
            continue
        names = [spec["name"] for spec in specs]
        if len(set(names)) != len(names):
            errors.append(f"Sheet {sheet_name!r} has duplicate column names")
            continue
        specs_by_sheet[sheet_name] = specs
        indexes[sheet_name] = {name: i for i, name in enumerate(names)}
        if version == 1 and ("primary_key" in sheet or "foreign_keys" in sheet):
            errors.append(f"Sheet {sheet_name!r}: relational constraints require schema_version 2")

    for sheet_name, sheet in sheets.items():
        specs = specs_by_sheet.get(sheet_name)
        if specs is None:
            continue
        positions = indexes[sheet_name]
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

        primary_key = None
        if "primary_key" in sheet:
            primary_key = _key_spec(sheet["primary_key"], f"Sheet {sheet_name!r} primary_key", errors)
            if primary_key:
                missing = set(primary_key) - set(positions)
                if missing:
                    errors.append(f"Sheet {sheet_name!r} primary_key references unknown columns: {sorted(missing)}")
                    primary_key = None
                else:
                    for column_name in primary_key:
                        spec = specs[positions[column_name]]
                        if spec.get("nullable", False):
                            errors.append(f"Sheet {sheet_name!r} primary_key column {column_name!r} cannot be nullable")
                    seen_keys: set[str] = set()
                    for row_number, row in enumerate(sheet["rows"], start=1):
                        values = tuple(row[positions[name]] for name in primary_key)
                        if any(value is None for value in values):
                            errors.append(f"Sheet {sheet_name!r}, row {row_number}: primary key contains null")
                            continue
                        marker = json.dumps(values, sort_keys=True, allow_nan=False)
                        if marker in seen_keys:
                            errors.append(f"Sheet {sheet_name!r}, row {row_number}: duplicate primary key {values!r}")
                        seen_keys.add(marker)

        if "foreign_keys" in sheet and not isinstance(sheet["foreign_keys"], list):
            errors.append(f"Sheet {sheet_name!r} foreign_keys must be an array")

    if version == 2:
        for sheet_name, sheet in sheets.items():
            if not isinstance(sheet.get("foreign_keys", []), list):
                continue
            local_positions = indexes.get(sheet_name)
            if local_positions is None:
                continue
            for fk_number, foreign_key in enumerate(sheet.get("foreign_keys", []), start=1):
                label = f"Sheet {sheet_name!r} foreign key {fk_number}"
                if not isinstance(foreign_key, dict) or set(foreign_key) - {"columns", "references", "on_delete"}:
                    errors.append(f"{label} must be an object with columns, references, and optional on_delete")
                    continue
                local_columns = _key_spec(foreign_key.get("columns"), f"{label} columns", errors)
                reference = foreign_key.get("references")
                if not isinstance(reference, dict) or set(reference) != {"sheet", "columns"}:
                    errors.append(f"{label} references must contain exactly sheet and columns")
                    continue
                target_sheet = reference["sheet"]
                target_columns = _key_spec(reference["columns"], f"{label} referenced columns", errors)
                policy = foreign_key.get("on_delete", "restrict")
                if policy not in DELETE_POLICIES:
                    errors.append(f"{label} has unsupported on_delete policy {policy!r}")
                if local_columns is None or target_columns is None:
                    continue
                if len(local_columns) != len(target_columns):
                    errors.append(f"{label} local and referenced key widths differ")
                    continue
                if set(local_columns) - set(local_positions):
                    errors.append(f"{label} references unknown local columns")
                    continue
                if target_sheet not in sheets or target_sheet not in indexes:
                    errors.append(f"{label} references unknown sheet {target_sheet!r}")
                    continue
                target_positions = indexes[target_sheet]
                if set(target_columns) - set(target_positions):
                    errors.append(f"{label} references unknown target columns")
                    continue

                target = sheets[target_sheet]
                target_pk = target.get("primary_key")
                target_key_is_unique = target_pk == target_columns
                if not target_key_is_unique and len(target_columns) == 1:
                    target_spec = specs_by_sheet[target_sheet][target_positions[target_columns[0]]]
                    target_key_is_unique = bool(target_spec.get("unique"))
                if not target_key_is_unique:
                    errors.append(f"{label} must reference a declared primary key or unique column")
                    continue

                target_values = {
                    tuple(row[target_positions[name]] for name in target_columns)
                    for row in target["rows"]
                }
                for row_number, row in enumerate(sheet["rows"], start=1):
                    values = tuple(row[local_positions[name]] for name in local_columns)
                    null_count = sum(value is None for value in values)
                    if null_count == len(values):
                        continue
                    if null_count:
                        errors.append(f"{label}, row {row_number}: composite foreign key is partially null")
                    elif values not in target_values:
                        errors.append(f"{label}, row {row_number}: referenced key {values!r} does not exist")

                if policy == "set_null":
                    for column_name in local_columns:
                        spec = specs_by_sheet[sheet_name][local_positions[column_name]]
                        if spec.get("nullable") is False:
                            errors.append(f"{label} set_null requires nullable local columns")

    return not errors, {"valid": not errors, "errors": errors}
