# XLSL schema v2: keys, relationships and migrations

Workbook schema version 1 remains supported. Version 2 adds declarative
primary keys and cross-sheet foreign keys. The ZIP package/container version
remains 1.0.0; container format and workbook schema versions are independent.

## Primary keys

Declare a single-column or composite key on a sheet:

```json
{
  "schema_version": 2,
  "sheets": {
    "Customers": {
      "primary_key": ["tenant_id", "customer_id"],
      "columns": [
        {"name": "tenant_id", "type": "string"},
        {"name": "customer_id", "type": "integer"},
        {"name": "name", "type": "string"}
      ],
      "rows": [["acme", 7, "Ada"]]
    }
  }
}
```

Primary-key values must be non-null and unique per row. Primary-key columns
cannot be declared nullable.

## Foreign keys

```json
{
  "columns": ["tenant_id", "customer_id"],
  "references": {
    "sheet": "Customers",
    "columns": ["tenant_id", "customer_id"]
  },
  "on_delete": "restrict"
}
```

Foreign keys live in a sheet's `foreign_keys` array. They must reference a
declared primary key or a single column declared `unique: true`. Composite
keys must have matching widths. A foreign-key tuple may be entirely null;
partially-null composite keys are invalid. Non-null references must resolve
to an existing target row.

Supported deletion policies are `restrict`, `cascade`, and `set_null`.
These are declarations only: this release validates their configuration but
does not delete rows or perform cascading mutations. `set_null` requires all
local columns to be nullable. A future transactional mutation API can enforce
the policies when deletion operations are introduced.

## Migration API

Migrations are explicit application-supplied functions. No implicit schema
conversion or package rewrite occurs.

```python
from xlsl import MigrationRegistry

registry = MigrationRegistry()

def add_metadata(workbook):
    workbook["sheets"]["Customers"]["columns"].append(
        {"name": "status", "type": "string", "nullable": True}
    )

registry.register(1, 2, add_metadata)
result = registry.migrate(workbook, 2)  # dry-run by default
preview = result.workbook
# Persist only after reviewing the preview, using write_xlsl().
```

The registry finds a deterministic shortest forward path, applies each step to
a deep copy, advances the schema version, and validates each intermediate
result. Missing paths and invalid outputs raise `XLSLFormatError`. The
`dry_run` flag is descriptive; migration never writes files, whether true or
false. The caller owns persistence and approval.

## Transaction-safe package updates

`update_xlsl(path, updater)` loads a package, passes a deep-copied workbook
to the updater, validates the result, writes a temporary package in the same
directory, and atomically replaces the original. If the updater or validation
fails, the original package remains untouched. The updater may mutate its
argument and return `None`, or return a replacement workbook object.

## Scope and safety

Validation is declarative. It does not execute formulas or embedded logic
modules. Referential checks happen in memory when a workbook is validated.
No row-deletion engine, cascade executor, SQL engine, or automatic migration
is introduced by this schema phase.
