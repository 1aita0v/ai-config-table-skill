#!/usr/bin/env python3
"""Copy a workbook and apply structured updates / appends.

Supports multi-row headers via patch JSON fields `field_row` and `meta_rows`.
The legacy `header_row` field is still accepted (treated as `field_row`).

Always run with --dry-run first to preview cell-level changes before writing.

The source workbook is never modified. Output is written to --output. If patching
fails partway through, the partial output file is removed.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any


def load_openpyxl():
    try:
        from openpyxl import load_workbook
        from openpyxl.styles import Font, PatternFill
        from openpyxl.utils import column_index_from_string, get_column_letter
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "openpyxl is required for Excel patching.\n"
            "Install with:  pip install openpyxl"
        ) from exc
    return load_workbook, Font, PatternFill, column_index_from_string, get_column_letter


load_workbook, Font, PatternFill, column_index_from_string, get_column_letter = load_openpyxl()
MARK_FILL = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
COL_RE = re.compile(r"^[A-Z]{1,3}$")


def norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def resolve_col(col: str | int) -> int:
    if isinstance(col, int):
        return col
    if isinstance(col, str) and col.isdigit():
        return int(col)
    return column_index_from_string(str(col))


def mark(cell) -> None:
    cell.fill = MARK_FILL
    old = cell.font
    cell.font = Font(
        name=old.name,
        size=old.size,
        bold=old.bold,
        italic=old.italic,
        color="000000",
        underline="single",
    )


def row_values(ws, row_idx: int) -> list[str]:
    return [norm(ws.cell(row=row_idx, column=col).value) for col in range(1, ws.max_column + 1)]


def guess_field_row(ws, scan_rows: int = 12) -> int:
    best_row = 1
    best_score = -1
    for row_idx in range(1, min(ws.max_row, scan_rows) + 1):
        row = row_values(ws, row_idx)
        values = [value for value in row if value]
        if not values:
            continue
        score = len(values) * 3 + len(set(values)) - row_idx
        if score > best_score:
            best_score = score
            best_row = row_idx
    return best_row


def header_map(ws, field_row: int) -> dict[str, int]:
    result: dict[str, int] = {}
    for col in range(1, ws.max_column + 1):
        name = norm(ws.cell(row=field_row, column=col).value)
        if name and name not in result:
            result[name] = col
    return result


def build_key_index(ws, key_col: int, data_start: int) -> dict[str, int]:
    index: dict[str, int] = {}
    for row_idx in range(data_start, ws.max_row + 1):
        value = norm(ws.cell(row=row_idx, column=key_col).value)
        if value and value not in index:
            index[value] = row_idx
    return index


def last_meaningful_row(ws, min_row: int) -> int:
    last = min_row - 1
    for row_idx in range(min_row, ws.max_row + 1):
        if any(row_values(ws, row_idx)):
            last = row_idx
    return last


def resolve_sheet_layout(sheet_patch: dict[str, Any], ws) -> tuple[int, list[int], int]:
    field_row = sheet_patch.get("field_row") or sheet_patch.get("header_row")
    field_row = int(field_row) if field_row else guess_field_row(ws)
    meta_rows = sheet_patch.get("meta_rows") or []
    meta_rows = [int(r) for r in meta_rows]
    declared_data_start = sheet_patch.get("data_start_row")
    if declared_data_start:
        data_start = int(declared_data_start)
    else:
        last_header = max([field_row] + meta_rows)
        data_start = last_header + 1
    return field_row, meta_rows, data_start


def collect_planned_changes(ws, sheet_patch: dict[str, Any]) -> dict[str, Any]:
    """Compute (but do not apply) the changes a patch would make. Used by --dry-run."""
    field_row, meta_rows, data_start = resolve_sheet_layout(sheet_patch, ws)
    header = header_map(ws, field_row)
    key_field = sheet_patch.get("key_field")
    key_col = header.get(key_field) if key_field else None
    key_index = build_key_index(ws, key_col, data_start) if key_col else {}

    planned_updates: list[dict[str, Any]] = []
    for update in sheet_patch.get("updates", []):
        if "row" in update and "col" in update:
            row = int(update["row"])
            col = resolve_col(update["col"])
        else:
            if not key_field:
                raise SystemExit(f"Sheet {ws.title}: key-based update requires key_field")
            if "key" not in update or "field" not in update:
                raise SystemExit(f"Sheet {ws.title}: update requires row/col or key/field")
            key = norm(update["key"])
            if key not in key_index:
                raise SystemExit(f"Key not found in {ws.title}: {key_field}={key}")
            row = key_index[key]
            field = update["field"]
            if field not in header:
                raise SystemExit(f"Field not found in {ws.title}: {field}")
            col = header[field]
        before = norm(ws.cell(row=row, column=col).value)
        planned_updates.append({"row": row, "col": col, "before": before, "after": norm(update.get("value"))})

    planned_appends: list[dict[str, Any]] = []
    append_start = last_meaningful_row(ws, data_start) + 1
    for row_offset, row_data in enumerate(sheet_patch.get("appends", [])):
        row_idx = append_start + row_offset
        cells: list[dict[str, Any]] = []
        for field, value in row_data.items():
            if field in header:
                col = header[field]
            elif str(field).isdigit() or COL_RE.match(str(field)):
                col = resolve_col(field)
            else:
                raise SystemExit(f"Append field not found in {ws.title}: {field}")
            cells.append({"col": col, "value": norm(value)})
        planned_appends.append({"row": row_idx, "cells": cells})

    return {
        "sheet": ws.title,
        "field_row": field_row,
        "meta_rows": meta_rows,
        "data_start_row": data_start,
        "updates": planned_updates,
        "appends": planned_appends,
    }


def apply_sheet_patch(ws, sheet_patch: dict[str, Any], should_mark: bool) -> dict[str, int]:
    field_row, meta_rows, data_start = resolve_sheet_layout(sheet_patch, ws)
    header = header_map(ws, field_row)
    key_field = sheet_patch.get("key_field")
    key_col = header.get(key_field) if key_field else None
    key_index = build_key_index(ws, key_col, data_start) if key_col else {}

    changed = 0
    appended = 0

    for update in sheet_patch.get("updates", []):
        if "row" in update and "col" in update:
            row = int(update["row"])
            col = resolve_col(update["col"])
        else:
            key = norm(update["key"])
            row = key_index[key]
            field = update["field"]
            col = header[field]
        cell = ws.cell(row=row, column=col)
        cell.value = update.get("value")
        if should_mark:
            mark(cell)
        changed += 1

    append_start = last_meaningful_row(ws, data_start) + 1
    for row_offset, row_data in enumerate(sheet_patch.get("appends", [])):
        row_idx = append_start + row_offset
        for field, value in row_data.items():
            if field in header:
                col = header[field]
            elif str(field).isdigit() or COL_RE.match(str(field)):
                col = resolve_col(field)
            else:
                raise SystemExit(f"Append field not found in {ws.title}: {field}")
            cell = ws.cell(row=row_idx, column=col)
            cell.value = value
            if should_mark:
                mark(cell)
            changed += 1
        appended += 1

    return {"changed_cells": changed, "appended_rows": appended}


def render_dry_run(plans: list[dict[str, Any]]) -> str:
    lines = ["# Patch Dry Run", ""]
    total_updates = total_appends = 0
    for plan in plans:
        lines.append(f"## Sheet: {plan['sheet']}")
        lines.append(
            f"  field_row={plan['field_row']} meta_rows={plan['meta_rows'] or '[]'} data_start_row={plan['data_start_row']}"
        )
        lines.append("")
        if plan["updates"]:
            lines.append("  Updates:")
            for u in plan["updates"]:
                before = u["before"] if u["before"] else "(empty)"
                lines.append(f"    row={u['row']} col={u['col']}: {before}  =>  {u['after']}")
                total_updates += 1
            lines.append("")
        if plan["appends"]:
            lines.append("  Appends:")
            for a in plan["appends"]:
                preview = ", ".join(f"col{c['col']}={c['value']}" for c in a["cells"][:8])
                lines.append(f"    row={a['row']}: {preview}")
                total_appends += 1
            lines.append("")
        if not plan["updates"] and not plan["appends"]:
            lines.append("  (no changes)")
            lines.append("")
    lines.append(f"Total: {total_updates} update(s), {total_appends} append row(s) across {len(plans)} sheet(s).")
    lines.append("Dry run only — source workbook was not modified, no output file written.")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Copy and patch an Excel workbook.")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--patch", type=Path, required=True, help="Patch JSON path.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing output.")
    parser.add_argument("--no-mark", action="store_true", help="Do not mark edited cells yellow.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned changes without writing the output file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.source.exists():
        raise SystemExit(f"Source not found: {args.source}")
    patch = json.loads(args.patch.read_text(encoding="utf-8"))

    if args.dry_run:
        wb = load_workbook(args.source, data_only=False, keep_vba=args.source.suffix.lower() == ".xlsm")
        plans = []
        for sheet_patch in patch.get("sheets", []):
            sheet_name = sheet_patch["sheet"]
            if sheet_name not in wb.sheetnames:
                raise SystemExit(f"Sheet not found: {sheet_name}")
            plans.append(collect_planned_changes(wb[sheet_name], sheet_patch))
        sys.stdout.write(render_dry_run(plans) + "\n")
        return

    if args.output.exists() and not args.force:
        raise SystemExit(f"Output already exists: {args.output}. Use --force to overwrite.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.source, args.output)

    try:
        wb = load_workbook(args.output, keep_vba=args.output.suffix.lower() == ".xlsm")
        summary = []
        for sheet_patch in patch.get("sheets", []):
            sheet_name = sheet_patch["sheet"]
            if sheet_name not in wb.sheetnames:
                raise SystemExit(f"Sheet not found: {sheet_name}")
            result = apply_sheet_patch(wb[sheet_name], sheet_patch, not args.no_mark)
            result["sheet"] = sheet_name
            summary.append(result)
        wb.save(args.output)
    except BaseException:
        # Remove partially-written output so the user does not trust a broken file.
        try:
            args.output.unlink(missing_ok=True)
        except Exception:
            pass
        raise

    sys.stdout.write(json.dumps({"output": str(args.output), "sheets": summary}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
