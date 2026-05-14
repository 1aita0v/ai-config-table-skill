"""Scan inventory data and surface 8 categories of "pattern candidates".

Output goes into inventory.md right after Project Memory, so the AI reads
script-detected patterns *before* it dives into file details. Every entry
is labeled "猜" — the AI is supposed to confirm with the user (and入档
via learn.py) before acting on it.

Categories
----------
1. 数字主键 ID 段分布      (numeric primary-key buckets)
2. 数组字段组              (Foo#N.Bar grouped by base name)
3. 跨 sheet 同名字段       (field names that appear in multiple sheets)
4. 公式分布摘要            (which sheets carry formulas, top by count)
5. 隐藏列警示              (no-header data columns)
6. LocKey / 命名模板候选   (regex hits on string samples)
7. 重复 sheet 名警告       (same sheet name across files)
8. 目录层级 / 业务分类     (path-tree summary + 新旧并行检测)

Design contracts
----------------
- All output is *advisory*, labelled "猜" / "候选".
- Pure aggregation over the inventory dict; no extra file reads.
- Returns Markdown ready for inclusion in inventory.md (or "" if no
  meaningful signal — silent on uninteresting projects).
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import PurePosixPath, PureWindowsPath
from typing import Any


# ---------------------------------------------------------------------------
# Category 1 — numeric primary-key buckets
# ---------------------------------------------------------------------------

_INT_RE = re.compile(r"^-?\d+$")


def _coerce_int(value: str) -> int | None:
    if _INT_RE.match(value.strip()):
        try:
            return int(value.strip())
        except (TypeError, ValueError):
            return None
    return None


def detect_id_buckets(values: list[int], min_gap_ratio: float = 10.0, min_segment_size: int = 2) -> list[dict[str, Any]]:
    """Group sorted integer keys into segments separated by big gaps.

    A "big gap" is one that's >= ``min_gap_ratio`` times the median gap.
    Returns a list of {min, max, count} dicts. Returns a single bucket
    (covering everything) when no big gaps exist — that signals "this table
    has a single contiguous ID range, nothing to ask".
    """
    if len(values) < 2:
        return [{"min": values[0], "max": values[0], "count": 1}] if values else []
    sorted_vals = sorted(values)
    gaps = [b - a for a, b in zip(sorted_vals, sorted_vals[1:])]
    positive_gaps = [g for g in gaps if g > 0]
    if not positive_gaps:
        return [{"min": sorted_vals[0], "max": sorted_vals[-1], "count": len(sorted_vals)}]
    sorted_gaps = sorted(positive_gaps)
    median_gap = sorted_gaps[len(sorted_gaps) // 2] or 1
    threshold = max(median_gap * min_gap_ratio, 2)
    segments: list[dict[str, Any]] = []
    current = [sorted_vals[0]]
    for prev, cur in zip(sorted_vals, sorted_vals[1:]):
        if cur - prev >= threshold:
            segments.append({"min": current[0], "max": current[-1], "count": len(current)})
            current = [cur]
        else:
            current.append(cur)
    segments.append({"min": current[0], "max": current[-1], "count": len(current)})
    # Drop tiny noise segments unless they're the only signal we have.
    big_segments = [s for s in segments if s["count"] >= min_segment_size]
    return big_segments if len(big_segments) >= 2 else segments


def summarize_id_buckets(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for file_info in inventory.get("files", []):
        for sheet in file_info.get("sheets", []):
            key_values = sheet.get("key_values") or []
            if not key_values:
                continue
            ints = [v for v in (_coerce_int(s) for s in key_values) if v is not None]
            if len(ints) < 5 or len(ints) < len(key_values) * 0.8:
                continue  # not predominantly numeric
            buckets = detect_id_buckets(ints)
            if len(buckets) >= 2:  # only report when multiple buckets — single contiguous range is uninteresting
                out.append({
                    "file": file_info.get("path"),
                    "sheet": sheet.get("name"),
                    "key_field": next((f.get("name") for f in sheet.get("fields", []) if f.get("key_candidate")), None),
                    "total_ids": len(ints),
                    "buckets": buckets,
                })
    return out


# ---------------------------------------------------------------------------
# Category 2 — array field groups (Foo#1.Bar / Foo#2.Bar)
# ---------------------------------------------------------------------------

_ARRAY_RE = re.compile(r"^(.+?)#(\d+)\.(.+)$")


def summarize_array_fields(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for file_info in inventory.get("files", []):
        for sheet in file_info.get("sheets", []):
            groups: dict[str, dict[str, Any]] = {}
            for field in sheet.get("fields", []):
                name = field.get("name") or ""
                match = _ARRAY_RE.match(name)
                if not match:
                    continue
                base, idx, sub = match.group(1), int(match.group(2)), match.group(3)
                bucket = groups.setdefault(base, {"max_index": 0, "subfields": set()})
                bucket["max_index"] = max(bucket["max_index"], idx)
                bucket["subfields"].add(sub)
            if groups:
                out.append({
                    "file": file_info.get("path"),
                    "sheet": sheet.get("name"),
                    "groups": [
                        {"base": base, "max_index": info["max_index"], "subfields": sorted(info["subfields"])}
                        for base, info in sorted(groups.items())
                    ],
                })
    return out


# ---------------------------------------------------------------------------
# Category 3 — cross-sheet same-name fields
# ---------------------------------------------------------------------------


def summarize_cross_sheet_fields(inventory: dict[str, Any], min_occurrences: int = 3, min_distinct_files: int = 2) -> list[dict[str, Any]]:
    """Cross-sheet field reuse.

    To avoid "I18N noise" — where one workbook holds 50+ sheets sharing the
    same Key / Lang#1.Val schema — only count fields that appear across
    **distinct files** ≥ ``min_distinct_files``. Same-file multi-sheet reuse
    is the I18N pattern and not a project-wide signal.
    """
    locations: dict[str, list[str]] = defaultdict(list)
    files_per_field: dict[str, set[str]] = defaultdict(set)
    for file_info in inventory.get("files", []):
        path = file_info.get("path") or ""
        for sheet in file_info.get("sheets", []):
            label = f"{path}#{sheet.get('name')}"
            for field in sheet.get("fields", []):
                name = field.get("name") or ""
                if not name:
                    continue
                locations[name].append(label)
                files_per_field[name].add(path)
    out: list[dict[str, Any]] = []
    for name, locs in sorted(locations.items(), key=lambda x: (-len(x[1]), x[0])):
        if len(locs) < min_occurrences:
            continue
        if len(files_per_field[name]) < min_distinct_files:
            continue  # all hits in one file (e.g. I18N's many sheets) — structural, not project signal
        out.append({
            "field": name,
            "count": len(locs),
            "distinct_files": len(files_per_field[name]),
            "locations": locs[:8],
            "truncated": len(locs) > 8,
        })
    return out


# ---------------------------------------------------------------------------
# Category 4 — formula distribution summary
# ---------------------------------------------------------------------------


def summarize_formula_distribution(inventory: dict[str, Any]) -> dict[str, Any] | None:
    sheets_with_formulas: list[dict[str, Any]] = []
    total_cells = 0
    for file_info in inventory.get("files", []):
        for sheet in file_info.get("sheets", []):
            count = sheet.get("formula_cells_observed", 0) or 0
            if count > 0:
                sheets_with_formulas.append({
                    "file": file_info.get("path"),
                    "sheet": sheet.get("name"),
                    "count": count,
                    "preview": sheet.get("formula_cells_preview") or [],
                })
                total_cells += count
    if not sheets_with_formulas:
        return None
    sheets_with_formulas.sort(key=lambda x: -x["count"])
    return {
        "sheet_count": len(sheets_with_formulas),
        "total_cells": total_cells,
        "top": sheets_with_formulas[:5],
    }


# ---------------------------------------------------------------------------
# Category 5 — hidden columns (no header, has data)
# ---------------------------------------------------------------------------


def summarize_hidden_columns(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for file_info in inventory.get("files", []):
        for sheet in file_info.get("sheets", []):
            hidden = sheet.get("hidden_columns") or []
            if not hidden:
                continue
            out.append({
                "file": file_info.get("path"),
                "sheet": sheet.get("name"),
                "columns": hidden,
            })
    return out


# ---------------------------------------------------------------------------
# Category 6 — LocKey / naming templates
# ---------------------------------------------------------------------------

# Patterns that suggest "this string is a LocKey reference, not literal text".
_LOCKEY_PATTERNS = [
    (re.compile(r"^[A-Z][A-Za-z]*_[A-Za-z]+_-?\d+$"), "<Word>_<Word>_<digits>"),
    (re.compile(r"^[A-Z]+_-?\d+_[A-Z]+$"), "<UPPER>_<digits>_<UPPER>"),
    (re.compile(r"^[a-z][a-z_]*_-?\d+$"), "<lower_words>_<digits>"),
    (re.compile(r"^[A-Z]{2,3}_[A-Za-z_]+(?:_-?\d+)?$"), "<UPPER>_<word>_<digits?>"),
]


def _classify_lockey(value: str) -> str | None:
    if not value or len(value) > 80:
        return None
    for pattern, label in _LOCKEY_PATTERNS:
        if pattern.match(value):
            return label
    return None


def summarize_lockey_templates(inventory: dict[str, Any], min_hits_per_field: int = 2) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for file_info in inventory.get("files", []):
        for sheet in file_info.get("sheets", []):
            per_field: dict[str, dict[str, list[str]]] = {}
            for sample in sheet.get("samples", []) or []:
                for field_name, value in sample.items():
                    if not isinstance(value, str):
                        continue
                    label = _classify_lockey(value)
                    if not label:
                        continue
                    bucket = per_field.setdefault(field_name, {})
                    examples = bucket.setdefault(label, [])
                    if value not in examples and len(examples) < 3:
                        examples.append(value)
            interesting = []
            for field_name, by_template in per_field.items():
                for label, examples in by_template.items():
                    if len(examples) >= min_hits_per_field:
                        interesting.append({"field": field_name, "template": label, "examples": examples})
            if interesting:
                out.append({
                    "file": file_info.get("path"),
                    "sheet": sheet.get("name"),
                    "hits": interesting,
                })
    return out


# ---------------------------------------------------------------------------
# Category 7 — duplicate sheet names across files
# ---------------------------------------------------------------------------


_DEFAULT_SHEET_NAMES = {"Sheet1", "Sheet2", "Sheet", "Sheet3", "sheet1"}


def summarize_duplicate_sheet_names(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    """Sheets that share a name across multiple files.

    Skips Excel's default ``Sheet1`` / ``Sheet2`` (collisions there are not
    a project signal, just default-name noise).
    """
    locations: dict[str, list[str]] = defaultdict(list)
    for file_info in inventory.get("files", []):
        for sheet in file_info.get("sheets", []):
            name = sheet.get("name") or ""
            if not name or name in _DEFAULT_SHEET_NAMES:
                continue
            locations[name].append(file_info.get("path", "?"))
    out: list[dict[str, Any]] = []
    for name, paths in sorted(locations.items()):
        unique_paths = sorted(set(paths))
        if len(unique_paths) > 1:
            out.append({"sheet": name, "files": unique_paths})
    return out


# ---------------------------------------------------------------------------
# Category 8 — directory tree + new/old parallel detection
# ---------------------------------------------------------------------------

# Keywords in folder names that signal "this might not be the canonical /
# production config" — covers new/old parallel, backup, dev/test/staging
# branches, draft/wip dirs, and version-tagged folders. Hit any of these →
# AI MUST ask the user which dir is the production source before touching
# tables.
_LEGACY_KEYWORDS = (
    "new", "old", "legacy", "deprecated", "obsolete",
    "backup", "archive", "snapshot",
    "dev", "test", "staging", "stage", "preview", "rc",
    "draft", "wip", "experiment", "experimental",
    "temp", "tmp", "scratch",
    "v1", "v2", "v3", "v4", "v5",
)


def _path_parts(path_str: str) -> list[str]:
    # Handle both / and \ separators.
    p = PurePosixPath(path_str.replace("\\", "/"))
    return list(p.parts)


def summarize_directory_layout(inventory: dict[str, Any]) -> dict[str, Any] | None:
    root = inventory.get("root") or ""
    root_parts = _path_parts(root) if root else []
    root_depth = len(root_parts)
    folder_stats: dict[str, dict[str, int]] = defaultdict(lambda: {"files": 0, "sheets": 0})
    filename_locations: dict[str, list[str]] = defaultdict(list)
    legacy_paths: list[str] = []
    for file_info in inventory.get("files", []):
        path_str = file_info.get("path", "")
        parts = _path_parts(path_str)
        rel_parts = parts[root_depth:] if parts[:root_depth] == root_parts else parts
        if not rel_parts:
            continue
        filename = rel_parts[-1]
        # 1st-level subdir under root (if any).
        if len(rel_parts) >= 2:
            top_folder = rel_parts[0]
            folder_stats[top_folder]["files"] += 1
            folder_stats[top_folder]["sheets"] += len(file_info.get("sheets", []))
        # Filename → list of containing paths (for duplicate filename detection).
        filename_locations[filename].append(path_str)
        # Legacy / new-style folder detection.
        for part in rel_parts[:-1]:
            if part.lower() in _LEGACY_KEYWORDS:
                legacy_paths.append(path_str)
                break
    duplicate_filenames = [
        {"filename": name, "files": sorted(set(paths))}
        for name, paths in sorted(filename_locations.items())
        if len(set(paths)) > 1
    ]
    if not folder_stats and not duplicate_filenames and not legacy_paths:
        return None
    return {
        "folders": sorted(
            ({"name": name, "files": s["files"], "sheets": s["sheets"]} for name, s in folder_stats.items()),
            key=lambda x: -x["files"],
        )[:20],
        "duplicate_filenames": duplicate_filenames[:25],
        "legacy_paths": sorted(set(legacy_paths))[:25],
    }


# ---------------------------------------------------------------------------
# Markdown renderer
# ---------------------------------------------------------------------------


def _bullet(text: str) -> str:
    return f"- {text}"


def _rel_path(full_path: str, root: str) -> str:
    """Shorten `<root>/foo/bar.xlsx` → `foo/bar.xlsx`, leave others untouched."""
    if not full_path:
        return full_path
    normalized_root = (root or "").rstrip("/\\")
    if normalized_root and full_path.startswith(normalized_root + "/"):
        return full_path[len(normalized_root) + 1:]
    if normalized_root and full_path.startswith(normalized_root + "\\"):
        return full_path[len(normalized_root) + 1:]
    return full_path


def render_md(inventory: dict[str, Any]) -> str:
    """Build the '配表规律候选' Markdown block. Returns '' when nothing interesting."""
    lines: list[str] = []
    root = inventory.get("root", "")
    id_buckets = summarize_id_buckets(inventory)
    array_fields = summarize_array_fields(inventory)
    cross_fields = summarize_cross_sheet_fields(inventory)
    formula = summarize_formula_distribution(inventory)
    hidden_cols = summarize_hidden_columns(inventory)
    lockey = summarize_lockey_templates(inventory)
    dup_sheets = summarize_duplicate_sheet_names(inventory)
    layout = summarize_directory_layout(inventory)

    sections: list[tuple[str, list[str]]] = []

    def rel(p: str) -> str:
        return _rel_path(p, root)

    if id_buckets:
        sec = ["这些 sheet 主键有明显的「段间跳跃」,**猜**:不同段对应不同业务类型。**先跟用户确认每段语义,再入档**。"]
        for entry in id_buckets[:8]:
            label = f"`{rel(entry['file'])}#{entry['sheet']}` 字段 `{entry['key_field']}` ({entry['total_ids']} 个 ID):"
            sec.append(_bullet(label))
            for b in entry["buckets"][:6]:
                sec.append(f"  - `[{b['min']:,} – {b['max']:,}]` × {b['count']} 个")
        sections.append(("数字主键 ID 段(候选业务分段)", sec))

    if array_fields:
        sec = ["数组列模式 `Foo#1.Bar` / `Foo#2.Bar` 在以下 sheet 出现 —— 改 / 加这些字段时**整组一起改**,不要漏 index。"]
        for entry in array_fields[:10]:
            groups_str = ", ".join(f"`{g['base']}` (最大 #{g['max_index']}, 子字段 {len(g['subfields'])} 个)" for g in entry["groups"][:5])
            sec.append(_bullet(f"`{rel(entry['file'])}#{entry['sheet']}`: {groups_str}"))
        sections.append(("数组字段组", sec))

    if cross_fields:
        sec = ["这些字段名在多个 sheet 出现,**猜**:可能是项目级公共字段,或跨表外键关联点。"]
        for entry in cross_fields[:10]:
            locs = ", ".join(f"`{rel(loc.split('#', 1)[0])}#{loc.split('#', 1)[1] if '#' in loc else ''}`" for loc in entry["locations"][:5])
            suffix = f" 等 {entry['count']} 处" if entry["truncated"] else ""
            sec.append(_bullet(f"`{entry['field']}` × {entry['count']}: {locs}{suffix}"))
        sections.append(("跨 sheet 同名字段", sec))

    if formula:
        sec = [f"共 **{formula['sheet_count']} 张 sheet** 含公式,公式格总数 **{formula['total_cells']:,}**。"]
        sec.append("公式分布 top 5:")
        for entry in formula["top"]:
            line = f"`{rel(entry['file'])}#{entry['sheet']}`: **{entry['count']} 格**"
            if entry["preview"]:
                line += f" — 例: `{entry['preview'][0]['formula']}`"
            sec.append(_bullet(line))
        sec.append("⚠️ 改这些表前先走 *公式闸门*,确认转值 / 沿用 / 导出无公式。")
        sections.append(("公式分布摘要", sec))

    if hidden_cols:
        sec = ["这些列**没有 header** 但数据行有内容 —— 通常是策划手写的备注列。**改表时绝对不能动这列**(开发工具按 header 名索引,看不到它)。"]
        for entry in hidden_cols[:10]:
            for col in entry["columns"][:3]:
                samples = ", ".join(f"`{v}`" for v in col["sample_values"])
                sec.append(_bullet(f"`{rel(entry['file'])}#{entry['sheet']}` col {col['col_index']}: 样本 {samples}"))
        sections.append(("隐藏列警示(无 header 有数据)", sec))

    if lockey:
        sec = ["string 字段值匹配 LocKey / 命名模板,**猜**:这是引用键,真实文本在另一张表(常见 I18N)。"]
        for entry in lockey[:8]:
            for hit in entry["hits"][:3]:
                examples = ", ".join(f"`{v}`" for v in hit["examples"])
                sec.append(_bullet(f"`{rel(entry['file'])}#{entry['sheet']}` 字段 `{hit['field']}` 形如 `{hit['template']}` (例: {examples})"))
        sections.append(("LocKey / 命名模板候选", sec))

    if dup_sheets:
        sec = ["同名 sheet 出现在多个文件,描述模糊时容易混淆 —— **用户说'某某表'时多确认一次**。"]
        for entry in dup_sheets[:30]:
            files_str = ", ".join(f"`{rel(p)}`" for p in entry["files"][:5])
            sec.append(_bullet(f"sheet `{entry['sheet']}`: {files_str}"))
        if len(dup_sheets) > 30:
            sec.append(_bullet(f"…还有 {len(dup_sheets) - 30} 条同名 sheet 未展开"))
        sections.append(("重复 sheet 名警告", sec))

    if layout:
        sec = []
        legacy = layout.get("legacy_paths") or []
        dup_files = layout.get("duplicate_filenames") or []
        if legacy or dup_files:
            sec.append("⚠️ **检测到「脏数据」信号** —— 项目里存在 new/old/dev/test/backup 等非正式目录,或同名文件并存在多个目录。**AI 第一件事:问用户**:")
            sec.append("")
            sec.append("> 我扫到下面这些目录看起来不是单一线上配置(`new/` / `backup/` / `dev/` 之类,或同名文件在不同目录都有)。开工前先确认:")
            sec.append("> - **哪个目录是当前正式 / 线上配置**(改动最终生效的那一份)?")
            sec.append("> - 其他目录是历史备份 / 在开发的下一版 / 实验沙盒 / 别的?")
            sec.append("> 答完我把「正式环境配置路径」记到 `<工程仓>/.ai-config-table/profile.md` 的 `baseline` 字段,下次自动应用。")
            sec.append("")
            sec.append("**用户确认前,禁止改这些目录里的任何表**(避免误改备份 / 实验 / 旧版)。")
            sec.append("")
        if layout.get("folders"):
            sec.append("**顶层子目录分布**(按文件数):")
            for f in layout["folders"]:
                sec.append(_bullet(f"`{f['name']}/` — {f['files']} 个文件 / {f['sheets']} 个 sheet"))
        if legacy:
            sec.append("")
            sec.append("**疑似非正式目录**(含 new/old/legacy/dev/test/backup/temp/wip 等关键字):")
            for p in legacy:
                sec.append(_bullet(f"`{rel(p)}`"))
        if dup_files:
            sec.append("")
            sec.append("**同名文件出现在不同目录**(可能是同一表的多版本,**别误改**):")
            for d in dup_files:
                files_str = ", ".join(f"`{rel(p)}`" for p in d["files"][:5])
                sec.append(_bullet(f"`{d['filename']}`: {files_str}"))
        if sec:
            sections.append(("目录层级 / 业务分类(+ 正式环境识别)", sec))

    if not sections:
        return ""

    lines.append("## 配表规律候选(脚本扫出来的线索,**未确认**)")
    lines.append("")
    lines.append("AI:下面每条都标了'猜'/'候选'。**任何要落地的规律,先跟用户确认再跑 `scripts/learn.py` 入档**,不要直接当事实用。已经在 `## Project Memory` 里被确认过的规律可跳过。")
    lines.append("")
    for idx, (title, body) in enumerate(sections, start=1):
        lines.append(f"### {idx}. {title}")
        lines.append("")
        lines.extend(body)
        lines.append("")
    return "\n".join(lines)
