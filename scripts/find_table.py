#!/usr/bin/env python3
"""Find tables / sheets / fields matching one or more keywords.

Use this when the user's description is fuzzy ("帮我改世界 boss 那张表") and
you don't know which physical sheet they mean. Instead of asking the user
upfront, **search the inventory you already have**, list 2-5 ranked
candidates with the matched evidence, and ask the user to pick.

Usage:
    # Run inspect first to produce an inventory.json (skip --patch-template here):
    python3 scripts/inspect_config_tables.py --root /path/to/config \\
        --format json --output /tmp/inv.json

    # Then find candidates for fuzzy keywords:
    python3 scripts/find_table.py --inventory /tmp/inv.json --keyword "boss,世界"

Scoring:
    sheet name match    → 5 points
    file name match     → 3 points
    field name match    → 2 points
    sample value match  → 1 point

The script ranks candidates by total score, prints the top N with the
reasons each matched. Output is Markdown by default (--format json
available).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Sibling module — relies on the script's directory being on sys.path[0].
from _config_loader import check_paths, load_config_file, merge_into_args


SCORE_SHEET_NAME = 5
SCORE_FILE_NAME = 3
SCORE_FIELD_NAME = 2
SCORE_SAMPLE_VALUE = 1


def keyword_in(text: str, keyword: str) -> bool:
    return keyword.lower() in text.lower()


def score_sheet(
    sheet: dict[str, Any], file_info: dict[str, Any], keywords: list[str]
) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []

    sheet_name = sheet.get("name", "") or ""
    for kw in keywords:
        if sheet_name and keyword_in(sheet_name, kw):
            score += SCORE_SHEET_NAME
            reasons.append(f"sheet name `{sheet_name}` contains `{kw}`")

    file_path = file_info.get("path", "") or ""
    file_stem = Path(file_path).stem if file_path else ""
    for kw in keywords:
        if file_stem and keyword_in(file_stem, kw):
            score += SCORE_FILE_NAME
            reasons.append(f"file name `{file_stem}` contains `{kw}`")

    for field in sheet.get("fields", []):
        fname = field.get("name", "") or ""
        for kw in keywords:
            if fname and keyword_in(fname, kw):
                score += SCORE_FIELD_NAME
                reasons.append(f"field `{fname}` contains `{kw}`")

    for sample in sheet.get("samples", [])[:3]:
        for k, v in sample.items():
            v_str = str(v) if v is not None else ""
            for kw in keywords:
                if v_str and keyword_in(v_str, kw):
                    snippet = v_str[:30] + ("..." if len(v_str) > 30 else "")
                    score += SCORE_SAMPLE_VALUE
                    reasons.append(f"sample value `{k}={snippet}` contains `{kw}`")

    return score, reasons


def render_md(
    keywords: list[str], candidates: list[dict[str, Any]], max_results: int
) -> str:
    lines = [f"# Find Table — keywords: {', '.join(keywords)}", ""]
    if not candidates:
        lines.append("**No candidates found.**")
        lines.append("")
        lines.append("Try simpler keywords or directly ask the user for a path / filename.")
        return "\n".join(lines)
    lines.append(
        f"Top {min(len(candidates), max_results)} of {len(candidates)} candidate sheet(s), "
        f"ranked by total score:"
    )
    lines.append("")
    for idx, c in enumerate(candidates[:max_results], 1):
        lines.append(f"## {idx}. `{c['sheet']}` in `{c['file']}` — score {c['score']}")
        lines.append("")
        lines.append("**Why matched:**")
        for r in c["reasons"][:6]:
            lines.append(f"- {r}")
        if len(c["reasons"]) > 6:
            lines.append(f"- ... +{len(c['reasons']) - 6} more match(es)")
        lines.append("")
        if c.get("fields"):
            preview = ", ".join(c["fields"][:10])
            more = f" (+{len(c['fields']) - 10} more)" if len(c["fields"]) > 10 else ""
            lines.append(f"**Fields:** {preview}{more}")
            lines.append("")
        if c.get("sample"):
            sample_preview = " | ".join(
                f"{k}={v}" for k, v in list(c["sample"].items())[:5]
            )
            lines.append(f"**Sample row:** {sample_preview}")
            lines.append("")
    lines.append(
        "**Next step:** pick the right one with the user, or fall back to "
        "directly asking them for a path if no candidate fits."
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Search an inventory.json for sheets/fields matching keywords."
    )
    parser.add_argument(
        "--inventory", type=Path, default=None,
        help="Path to an inventory.json produced by inspect_config_tables.py. (Required, "
             "but can also be provided via --config.)",
    )
    parser.add_argument(
        "--keyword", type=str, default="",
        help='Comma-separated keywords to search, e.g. "boss,世界,WorldBoss".',
    )
    parser.add_argument(
        "--max-results", type=int, default=5,
        help="Number of top candidates to show (default 5).",
    )
    parser.add_argument(
        "--format", choices=("md", "json"), default="md",
        help="Output format (default: md).",
    )
    parser.add_argument("--output", type=Path, default=None, help="Write report to a file.")
    parser.add_argument(
        "--config", type=Path, default=None,
        help="Read all params from a UTF-8 JSON config file (use on Windows when paths "
             "contain non-ASCII characters).",
    )
    args = parser.parse_args()
    cfg = load_config_file(args.config)
    merge_into_args(args, cfg, path_fields=("inventory", "output"), list_fields=("keyword",))
    check_paths(args, ("inventory", "output", "config"))
    return args


def main() -> None:
    args = parse_args()
    if args.inventory is None:
        raise SystemExit(
            "--inventory is required (run inspect_config_tables.py with --format json "
            "first to produce one)."
        )
    if not args.inventory.exists():
        raise SystemExit(f"Inventory not found: {args.inventory}")

    # --keyword can arrive as a string (CLI) or list (from --config JSON).
    if isinstance(args.keyword, list):
        keywords = [str(k).strip() for k in args.keyword if str(k).strip()]
    else:
        keywords = [k.strip() for k in args.keyword.split(",") if k.strip()]
    if not keywords:
        raise SystemExit("--keyword is required (comma-separated, e.g. \"boss,世界\").")

    inventory = json.loads(args.inventory.read_text(encoding="utf-8"))

    candidates: list[dict[str, Any]] = []
    for file_info in inventory.get("files", []):
        for sheet in file_info.get("sheets", []):
            score, reasons = score_sheet(sheet, file_info, keywords)
            if score <= 0:
                continue
            candidates.append(
                {
                    "file": file_info.get("path"),
                    "sheet": sheet.get("name"),
                    "score": score,
                    "reasons": reasons,
                    "fields": [f.get("name") for f in sheet.get("fields", [])],
                    "sample": (sheet.get("samples") or [{}])[0],
                }
            )

    candidates.sort(key=lambda c: -c["score"])

    if args.format == "json":
        text = json.dumps(
            {"keywords": keywords, "total_candidates": len(candidates), "candidates": candidates[: args.max_results]},
            ensure_ascii=False,
            indent=2,
        )
    else:
        text = render_md(keywords, candidates, args.max_results)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
