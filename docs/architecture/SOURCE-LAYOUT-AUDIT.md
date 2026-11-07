# Source and dependency layout audit

**Audited ref:** `main` at `440fa5c7fa93b78e1f4502da3599e8700f03685e`  
**Scope:** source, tests, schema, notebooks, package metadata, and GitHub Actions.  
**Purpose:** establish safe ownership boundaries before any source-tree moves.

## Executive result

The repository is currently a mixed workspace, not a single cohesive Python package. The native XLSL package is the clearest stable boundary. Other directories contain separate workbook utilities, AI/research experiments, quantum/telecom examples, web/backend fragments, and legacy or incomplete application code. No broad source-directory moves are recommended until ownership and execution contracts are established.

## Classification

| Path | Observed responsibility | Recommendation |
|---|---|---|
| `xlsl/` | Native XLSL ZIP package reader/writer, validation, migrations | Keep as the canonical XLSL runtime package |
| `tests/test_xlsl_*.py` | Tests for package safety, typed schema, relations, migrations | Keep grouped as the XLSL test suite; do not move until unittest discovery and CI paths are updated together |
| `src/file_loader.py`, `src/validators.py` | Legacy pandas/openpyxl workbook loader and YAML-driven validation | Treat as a separate legacy workbook-validation path; do not merge into `xlsl.validation` without an explicit compatibility design |
| `schema/aura_schema.yaml` | Legacy workbook sheet/column schema consumed by `src/file_loader.py` | Keep at its current path; the loader references it as `schema/aura_schema.yaml` |
| `tests/test_validate_workbook.py` | Legacy validator test | Keep with legacy validator for now; its fixture path `data/Aura.xlsl` needs reconciliation with the current workbook location |
| `src/demo_ai_sim_*.py`, `src/ai_data_setup.py`, `src/config_circuit.py`, `src/quantum_pipeline.py` | AI, simulation, and quantum experiments | Separate experimental domain; dependencies and entry points need their own inventory |
| `src/setup_telecom.py`, `src/telecoms_excel.py` | Telecom path optimization / Excel integration | Separate telecom domain; do not classify as core XLSL runtime |
| `src/app.tsx`, `src/backend/`, `src/frontend/`, `src/web/`, `backend/` | Web and backend fragments in multiple languages | Treat as separate application surfaces; map actual build roots before moving |
| `core/`, `aura-core/`, `AuraQuantum/`, `AI/`, `app/` | Mixed Ruby/Python/JS/Swift, quantum, model assets, and app code | Preserve untouched pending ownership and import/build graph review |
| `notebooks/` | Workbook, notebook, R analysis, and exploration assets | Keep notebook-oriented assets here; identical notebook copies remain pending provenance review |
| `docs/`, `Docs/` | Mixed product documentation and unrelated technical documents | Continue only file-by-file moves with verified ownership |

## Dependency and correctness findings

### 1. Two different workbook validation systems

- `src/file_loader.py` loads Excel workbooks through pandas and validates sheet/column requirements from `schema/aura_schema.yaml`.
- `xlsl/validation.py` validates the native XLSL JSON workbook model, typed columns, and schema-v2 relational constraints.
- These are distinct data models and APIs. They should not be collapsed into one validator as a cleanup-only change.
- The YAML schema uses a `required` property, while the native XLSL validator has its own typed-schema vocabulary. A future adapter needs explicit mapping and tests.

### 2. Import-time side effects in `src/__init__.py`

Importing `src` currently opens a workbook at the absolute path `/mnt/data/Aura_Hub.xlsx`, edits cells, and writes another workbook. This means even importing `src.validators` executes workbook mutation code before the validator import completes. This is a high-priority correctness issue to isolate before any package restructuring. The safe remediation should make package initialization inert and move workbook generation behind an explicit function/CLI entry point, with tests.

### 3. Legacy validator fixture path is stale

`tests/test_validate_workbook.py` validates `data/Aura.xlsl`, while the repository's organized workbook assets are under `data/workbooks/`. This test path and the loader's schema path need a deliberate fixture/root-path decision. No path change was made in this audit.

### 4. Package metadata is not trustworthy for this repository

- `pyproject.toml` still describes Automated Radio and uses `package-mode = false`.
- `script/setup.py` contains two consecutive `setup()` calls with different distribution names and dependency lists.
- Root `requirements.txt` contains duplicate entries and mixes scientific, notebook, web, and GPU dependencies.
- Do not replace author, license, package name, or dependency metadata by assumption. First decide whether this repository is a monorepo/workspace or whether one product is the installable distribution.

### 5. Broken or stale workflow references

- `.github/workflows/validate-data.yml` runs in `script/validate-data`, but that directory currently contains only a one-byte `package-lock.json`; the referenced `index.ts` and a package manifest are absent.
- `.github/workflows/validate_data.yml` calls `scripts/validate_aura_data.py`, which is absent from the current `scripts/` directory.
- The XLSL workflows have branch-specific push filters for old feature branches. Pull-request triggers remain, but direct pushes to `main` do not run those jobs under the current branch filters.
- The typed-schema workflow still watches the old `docs/XLSL-V1-TYPED-SCHEMA.md` path even though the document was moved under `docs/specification/`.
- These should be repaired in a dedicated CI change after agreeing which validation jobs are authoritative.

### 6. Notebook duplication

`notebooks/Aura_Hub.ipynb` and `notebooks/Aura_Hub 2.ipynb` currently have the same Git blob SHA. They are byte-identical at the audited ref. They are intentionally retained until the desired canonical filename and any external references are confirmed.

## Recommended execution order

1. Make `src/__init__.py` import-safe; preserve its workbook-generation behavior behind an explicit callable entry point and add a regression test.
2. Fix the legacy validator fixture path and test from a repository-root-independent path strategy.
3. Repair or retire the two stale data-validation workflows, and update XLSL workflow branch/path filters.
4. Decide the repository packaging model; then replace stale Poetry/setuptools metadata and deduplicate dependencies by runtime group.
5. Split the remaining mixed source areas only after recording their imports, entry points, data paths, and runtime dependencies.
6. Revisit duplicate notebook/workbook assets only with provenance evidence.

## Changes made by this audit

Documentation only. No source files, tests, schemas, notebooks, package metadata, or workflows were moved or modified. No tests were run because this audit commit contains no executable changes and the repository cannot be executed through the GitHub read/write connector.