# Data Sources

Use this reference when deciding how to read a project's configuration tables.

## Source Selection

Prefer sources in this order:

1. Project-declared source of truth.
2. Local source Excel/CSV/TSV/JSON files.
3. Project export files, only if docs confirm they are authoritative.
4. Cloud sheets or table platforms with read/export access.
5. Project-provided table tools or APIs.
6. User-provided sample files.

Do not write to a remote source unless the user explicitly asks for writeback and the workflow has passed validation.

If no source can be reached, use `no-data-source-report.md`. A clean failure is better than a confident guess.

## Local Files

Use `scripts/inspect_config_tables.py` on a config root or selected files:

```bash
python3 scripts/inspect_config_tables.py --root path/to/config --format md --output inventory.md
python3 scripts/inspect_config_tables.py --root path/to/config --format json --output inventory.json
```

The script supports `.xlsx`, `.xlsm`, `.csv`, `.tsv`, and `.json`.

## Exported Files

Exports are useful for discovery and diffing. Before editing from an export, confirm whether the export is authoritative or generated from another source.

Record:

- export path
- export time
- source project/table name
- whether formulas/styles are preserved
- whether hidden columns/sheets are included

## Cloud Sheets

For shared spreadsheets, online databases, admin panels, or custom table platforms:

- Use read/list/query APIs for discovery.
- Export copies for heavy diffing if available.
- Preserve table IDs, view IDs, sheet IDs, and revision info in the spec.
- Treat visible column names and internal field IDs as separate facts.

## Project Tools And APIs

Many teams already have scripts for exporting, validating, or publishing config. Prefer those over generic editing when available.

Look for:

- `export`, `dump`, `build`, `validate`, `lint`, `check`, `publish` scripts
- schema files
- generated client/server data
- table dictionaries
- README or docs near config folders

## Evidence To Record

Always record:

- source type and path/tool name
- project/table/workbook/sheet identifiers
- query/filter used
- timestamp
- row count or used range
- sample row IDs
- export temp path, if any
