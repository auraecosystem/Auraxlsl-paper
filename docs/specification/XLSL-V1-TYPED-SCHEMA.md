# XLSL v1 typed workbook schema

XLSL package version 1.0.0 supports workbook schema version 1. The package
version controls the archive/container contract; schema_version controls
column metadata and validation semantics.

## Backward compatibility

Existing sheets may continue to declare columns as strings:

    "columns": ["sample_id", "reading"]

String-only declarations remain untyped. New documents may declare typed
columns:

    {
      "schema_version": 1,
      "sheets": {
        "Measurements": {
          "columns": [
            {"name": "sample_id", "type": "string", "nullable": false,
             "unique": true, "pattern": "[A-Z0-9-]+"},
            {"name": "reading", "type": "number", "nullable": false,
             "minimum": 0, "maximum": 1000},
            {"name": "observed_on", "type": "date", "nullable": true}
          ],
          "rows": [["SAMPLE-01", 21.5, "2026-11-07"]]
        }
      }
    }

## Supported types

- string: UTF-8 JSON string.
- integer: JSON integer; booleans are not integers for this contract.
- number: finite JSON integer or floating-point number; booleans excluded.
- boolean: JSON boolean.
- date: ISO-8601 calendar date string.
- datetime: ISO-8601 datetime string; Z UTC suffix is accepted.
- json: any JSON value.

## Column properties

| Property | Meaning |
|---|---|
| name | Required column name |
| type | Required type for typed columns |
| nullable | Defaults to false for typed columns |
| unique | Enforces uniqueness among non-null values in the column |
| minimum / maximum | Inclusive numeric bounds |
| enum | Allowed exact values |
| pattern | Python regular expression, full-string match; string columns only |

Unknown column properties and unsupported types are rejected. String-only legacy
columns remain untyped, preserving compatibility with the initial package API.

## Validation API

    from xlsl import validate_workbook
    valid, report = validate_workbook(workbook)
    if not valid:
        raise ValueError(report["errors"])

The package reader and writer validate schema version and typed cells as well
as the base row/column shape. Validation is declarative: it does not evaluate
formulas, execute logic modules, or resolve cross-sheet references.

## Schema evolution policy

- schema_version defaults to 1 when omitted.
- Readers reject unsupported schema versions rather than guessing.
- Additive optional metadata may be introduced without changing the package
  container version when validation semantics remain compatible.
- Changes to type meaning, null semantics, or constraint behavior require a
  schema-version increment and a documented migration.
- A future migration utility must be explicit and must never silently rewrite
  source packages.
