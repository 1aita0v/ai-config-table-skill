#!/usr/bin/env python3
"""Scan a directory of config tables and emit an inventory.

Supports .xlsx, .xlsm, .csv, .tsv, .json.

Multi-row headers: pass --field-row N (1-based) to mark which row holds the
machine-readable field names, and --meta-rows R1,R2,... for extra header rows
(Chinese display name, type annotation, comment, etc.). If both are omitted the
script falls back to guessing a single-row header from the first 12 rows.

Encoding fallback: CSV/TSV/JSON files are first read as UTF-8 (with BOM tolerance);
on UnicodeDecodeError the script retries with GBK and records the encoding used
in the per-file output.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable


SUPPORTED = {".xlsx", ".xlsm", ".csv", ".tsv", ".json"}

KEY_EXACT = {"id", "key", "编号", "主键", "uid"}
KEY_SUFFIX_RE = re.compile(r"_id$", re.IGNORECASE)
KEY_CAMEL_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]*ID$")

ENCODING_FALLBACKS = ("utf-8-sig", "utf-8", "gbk", "gb18030")
SKILL_VERSION = "3"


def load_openpyxl():
    try:
        from openpyxl import load_workbook
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "openpyxl is required for Excel files.\n"
            "Install with:  pip install openpyxl\n"
            "Or restrict --root to CSV/TSV/JSON files only."
        ) from exc
    return load_workbook


def norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("\r\n", "\n").replace("\r", "\n").strip()


def trim(row: list[str]) -> list[str]:
    while row and row[-1] == "":
        row.pop()
    return row


def nonempty(row: list[str]) -> int:
    return sum(1 for value in row if value)


def is_key_candidate(name: str) -> bool:
    if not name:
        return False
    low = name.strip().lower()
    if low in KEY_EXACT:
        return True
    if KEY_SUFFIX_RE.search(name):
        return True
    if KEY_CAMEL_RE.match(name):
        return True
    return False


def guess_header(rows: list[list[str]], scan_rows: int) -> int:
    best_idx = 0
    best_score = -1
    for idx, row in enumerate(rows[:scan_rows]):
        values = [value for value in row if value]
        if not values:
            continue
        unique = len(set(values))
        score = len(values) * 3 + unique - idx
        if score > best_score:
            best_idx = idx
            best_score = score
    return best_idx


def field_summary(headers: list[str]) -> list[dict[str, Any]]:
    result = []
    for idx, name in enumerate(headers, start=1):
        if not name:
            continue
        result.append({"index": idx, "name": name, "key_candidate": is_key_candidate(name)})
    return result


def sample_rows(rows: list[list[str]], data_start_idx: int, headers: list[str], sample_count: int) -> list[dict[str, str]]:
    samples = []
    for row in rows[data_start_idx:]:
        if nonempty(row) == 0:
            continue
        item = {}
        for idx, name in enumerate(headers):
            if not name:
                continue
            value = row[idx] if idx < len(row) else ""
            if value:
                item[name] = value
        if item:
            samples.append(item)
        if len(samples) >= sample_count:
            break
    return samples


def iter_config_files(root: Path, max_files: int) -> Iterable[Path]:
    if root.is_file():
        if root.suffix.lower() in SUPPORTED:
            yield root
        return
    count = 0
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED:
            yield path
            count += 1
            if count >= max_files:
                return


def decode_with_fallback(data: bytes, prefer: str) -> tuple[str, str]:
    encodings = (prefer,) + tuple(e for e in ENCODING_FALLBACKS if e != prefer)
    last_err: UnicodeDecodeError | None = None
    for enc in encodings:
        try:
            return data.decode(enc), enc
        except UnicodeDecodeError as exc:
            last_err = exc
            continue
    raise last_err if last_err else UnicodeDecodeError(prefer, b"", 0, 1, "all encodings failed")


def resolve_header_layout(
    rows: list[list[str]],
    field_row_1based: int | None,
    meta_rows_1based: list[int],
    header_scan_rows: int,
) -> tuple[int, int, list[str]]:
    if field_row_1based is not None:
        field_idx = field_row_1based - 1
        if field_idx < 0:
            field_idx = 0
        if field_idx >= len(rows):
            field_idx = max(len(rows) - 1, 0)
        headers = rows[field_idx] if field_idx < len(rows) else []
        last_header_row = max([field_idx] + [r - 1 for r in meta_rows_1based])
        data_start = last_header_row + 1
        return field_idx, data_start, headers
    field_idx = guess_header(rows, header_scan_rows)
    headers = rows[field_idx] if rows else []
    return field_idx, field_idx + 1, headers


def inspect_delimited(path: Path, delimiter: str, args: argparse.Namespace) -> dict[str, Any]:
    data = path.read_bytes()
    text, encoding = decode_with_fallback(data, args.encoding)
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    rows: list[list[str]] = []
    for idx, row in enumerate(reader):
        rows.append(trim([norm(cell) for cell in row[: args.max_cols]]))
        if idx + 1 >= args.max_scan_rows:
            break
    field_idx, data_start, headers = resolve_header_layout(
        rows, args.field_row, args.meta_rows, args.header_scan_rows
    )
    return {
        "type": path.suffix.lower().lstrip("."),
        "path": str(path),
        "encoding": encoding,
        "sheets": [
            {
                "name": path.stem,
                "observed_rows": len(rows),
                "observed_cols": max((len(row) for row in rows), default=0),
                "field_row": field_idx + 1,
                "header_row": field_idx + 1,
                "meta_rows": list(args.meta_rows) if args.meta_rows else [],
                "data_start_row": data_start + 1,
                "fields": field_summary(headers),
                "samples": sample_rows(rows, data_start, headers, args.sample_rows),
            }
        ],
    }


def inspect_json(path: Path, args: argparse.Namespace) -> dict[str, Any]:
    data = path.read_bytes()
    text, encoding = decode_with_fallback(data, args.encoding)
    payload = json.loads(text)
    rows = payload if isinstance(payload, list) else payload.get("rows", []) if isinstance(payload, dict) else []
    fields = []
    samples = []
    if rows and isinstance(rows[0], dict):
        names = sorted({key for row in rows[: args.sample_rows] for key in row.keys()})
        fields = field_summary(names)
        for row in rows[: args.sample_rows]:
            samples.append({str(k): norm(v) for k, v in row.items() if norm(v)})
    return {
        "type": "json",
        "path": str(path),
        "encoding": encoding,
        "sheets": [
            {
                "name": path.stem,
                "observed_rows": len(rows) if isinstance(rows, list) else 0,
                "observed_cols": len(fields),
                "field_row": None,
                "header_row": None,
                "meta_rows": [],
                "data_start_row": None,
                "fields": fields,
                "samples": samples,
            }
        ],
    }


def inspect_excel(path: Path, args: argparse.Namespace) -> dict[str, Any]:
    load_workbook = load_openpyxl()
    wb = load_workbook(path, read_only=True, data_only=False, keep_vba=path.suffix.lower() == ".xlsm")
    sheets = []
    for ws in wb.worksheets[: args.max_sheets]:
        rows: list[list[str]] = []
        for idx, row in enumerate(ws.iter_rows(values_only=True)):
            rows.append(trim([norm(cell) for cell in row[: args.max_cols]]))
            if idx + 1 >= args.max_scan_rows:
                break
        field_idx, data_start, headers = resolve_header_layout(
            rows, args.field_row, args.meta_rows, args.header_scan_rows
        )
        sheets.append(
            {
                "name": ws.title,
                "declared_rows": ws.max_row,
                "declared_cols": ws.max_column,
                "observed_rows": len(rows),
                "observed_cols": max((len(row) for row in rows), default=0),
                "field_row": field_idx + 1,
                "header_row": field_idx + 1,
                "meta_rows": list(args.meta_rows) if args.meta_rows else [],
                "data_start_row": data_start + 1,
                "fields": field_summary(headers),
                "samples": sample_rows(rows, data_start, headers, args.sample_rows),
            }
        )
    return {"type": path.suffix.lower().lstrip("."), "path": str(path), "encoding": "binary", "sheets": sheets}


def inspect_file(path: Path, args: argparse.Namespace) -> dict[str, Any]:
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xlsm"}:
        return inspect_excel(path, args)
    if suffix == ".csv":
        return inspect_delimited(path, ",", args)
    if suffix == ".tsv":
        return inspect_delimited(path, "\t", args)
    if suffix == ".json":
        return inspect_json(path, args)
    raise SystemExit(f"Unsupported file: {path}")


def render_md(inventory: dict[str, Any]) -> str:
    lines = [
        "# Config Inventory",
        "",
        f"- Root: `{inventory['root']}`",
        f"- Files: {len(inventory['files'])}",
        f"- Generated by: ai-config-table v{inventory['skill_version']}",
        "",
    ]
    for file_info in inventory["files"]:
        lines.append(f"## {file_info['path']}")
        lines.append("")
        if file_info.get("encoding") and file_info["encoding"] != "binary":
            lines.append(f"- Encoding: `{file_info['encoding']}`")
        if "error" in file_info:
            lines.append(f"- ERROR: {file_info['error']}")
            lines.append("")
            continue
        for sheet in file_info["sheets"]:
            size_rows = sheet.get("declared_rows", sheet.get("observed_rows"))
            size_cols = sheet.get("declared_cols", sheet.get("observed_cols"))
            field_row = sheet.get("field_row")
            meta_rows = sheet.get("meta_rows") or []
            data_start = sheet.get("data_start_row")
            header_info = f"field_row={field_row}"
            if meta_rows:
                header_info += f" meta_rows={','.join(str(r) for r in meta_rows)}"
            if data_start:
                header_info += f" data_start={data_start}"
            lines.append(f"- Sheet: `{sheet['name']}` rows={size_rows} cols={size_cols} {header_info}")
            keys = [f["name"] for f in sheet["fields"] if f["key_candidate"]]
            if keys:
                lines.append(f"  - Key candidates: {', '.join(keys)}")
            field_names = [f["name"] for f in sheet["fields"]]
            lines.append(f"  - Fields: {', '.join(field_names[:40])}")
            if sheet["samples"]:
                first = sheet["samples"][0]
                preview = " | ".join(f"{k}={v}" for k, v in list(first.items())[:8])
                lines.append(f"  - Sample: {preview}")
        lines.append("")
    return "\n".join(lines)


def parse_meta_rows(value: str) -> list[int]:
    if not value:
        return []
    parts = [p.strip() for p in value.split(",") if p.strip()]
    try:
        return [int(p) for p in parts]
    except ValueError as exc:
        raise SystemExit(f"--meta-rows expects comma-separated integers, got: {value}") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect local configuration tables.")
    parser.add_argument("--root", type=Path, required=True, help="Config root or single file.")
    parser.add_argument("--output", type=Path, help="Output path.")
    parser.add_argument("--format", choices=("json", "md"), default="json")
    parser.add_argument(
        "--field-row",
        type=int,
        default=None,
        help="1-based row index holding machine-readable field names. Omit to auto-guess.",
    )
    parser.add_argument(
        "--meta-rows",
        type=str,
        default="",
        help="Comma-separated 1-based row indices for supplementary header rows, e.g. 1,3,4.",
    )
    parser.add_argument("--max-files", type=int, default=200)
    parser.add_argument("--max-sheets", type=int, default=80)
    parser.add_argument("--max-scan-rows", type=int, default=200)
    parser.add_argument("--header-scan-rows", type=int, default=12)
    parser.add_argument("--max-cols", type=int, default=80)
    parser.add_argument("--sample-rows", type=int, default=3)
    parser.add_argument(
        "--encoding",
        default="utf-8-sig",
        help="Preferred text encoding for CSV/TSV/JSON. Falls back to utf-8 / gbk / gb18030 on failure.",
    )
    args = parser.parse_args()
    args.meta_rows = parse_meta_rows(args.meta_rows)
    return args


def main() -> None:
    args = parse_args()
    if not args.root.exists():
        raise SystemExit(f"Root not found: {args.root}")
    files = []
    for path in iter_config_files(args.root, args.max_files):
        try:
            files.append(inspect_file(path, args))
        except Exception as exc:
            files.append({"type": path.suffix.lower().lstrip("."), "path": str(path), "error": str(exc), "sheets": []})
    inventory = {"root": str(args.root), "skill_version": SKILL_VERSION, "files": files}
    text = json.dumps(inventory, ensure_ascii=False, indent=2) if args.format == "json" else render_md(inventory)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
