# XLSL v1 package format

**Status:** initial implementation contract  
**Format identifier:** XLSL  
**Package version:** 1.0.0  
**File extension:** .xlsl

## Purpose

An XLSL file is a ZIP-based package containing structured workbook data, a
versioned manifest, and optional language-source modules. It is not an ordinary
Excel workbook with a renamed extension.

The package separates data from executable-language design. Version 1 readers
preserve optional logic source as UTF-8 text but **never execute it**. A parser,
type system, permissions model, and runtime are separate future specifications.

## Package layout

    research.xlsl
    ├── manifest.json
    ├── workbook.json
    └── logic/
        └── analysis.xsl   (optional, inert source text in v1)

Only manifest.json, workbook.json, and files below logic/ ending in .xsl are
permitted. Unknown package entries are rejected rather than silently ignored.

## Manifest

    {
      "format": "XLSL",
      "format_version": "1.0.0"
    }

The reader rejects unknown format identifiers and unsupported format versions.
Additional manifest metadata may be added compatibly in later 1.0 revisions.

## Workbook data

    {
      "sheets": {
        "Measurements": {
          "columns": ["sample_id", "temperature_c"],
          "rows": [
            ["sample-001", 21.5],
            ["sample-002", 22.1]
          ]
        }
      }
    }

Rules:

- sheets is a non-empty object.
- Each sheet has a non-empty name, a columns array of unique non-empty strings,
  and a rows array.
- Every row is an array whose length exactly matches the number of columns.
- Cell values must be JSON values. Non-standard JSON numbers such as NaN and
  Infinity are rejected by the writer.
- Domain-level types, constraints, formulas, relationships, and schema evolution
  are not inferred by this structural contract.

## Safety requirements

The reference reader:

- reads members directly and never extracts archive paths to disk;
- rejects absolute paths, traversal segments, backslashes, duplicate entries,
  symbolic links, encrypted entries, and unknown members;
- limits packages to 256 entries, 16 MiB per member, and 32 MiB total
  uncompressed data;
- requires UTF-8 JSON and rejects duplicate JSON object keys;
- rejects unsupported format versions;
- treats all logic modules as inert text.

These limits are implementation defaults, not permission to execute or trust
package content. Applications should still apply their own resource and access
policies.

## Python API

    from xlsl import XLSLDocument, read_xlsl, write_xlsl

    document = XLSLDocument(
        workbook={
            "sheets": {
                "Measurements": {
                    "columns": ["sample_id", "temperature_c"],
                    "rows": [["sample-001", 21.5]],
                }
            }
        }
    )

    write_xlsl(document, "research.xlsl")
    loaded = read_xlsl("research.xlsl")
    print(loaded.workbook["sheets"]["Measurements"]["rows"])

## Compatibility boundary

- .xlsx remains an Office Open XML workbook format.
- .xlsl is this native XLSL package format; changing an extension does not
  convert an existing Excel workbook.
- Existing historical documents describing other extensions are not changed by
  this v1 contract.
- The XLSL language grammar and execution runtime are explicitly out of scope
  for v1. The .xsl module suffix is a reserved source-module convention here,
  not a claim that a compiler or interpreter exists.
