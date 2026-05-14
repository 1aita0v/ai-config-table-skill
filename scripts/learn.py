#!/usr/bin/env python3
"""Append a learned pattern to ``.ai-config-table/learned-patterns.md``.

This is how the skill gets smarter over time on a per-project basis. The
agent observes a stable rule, **asks the user** whether to save it, and
runs this script only after explicit approval. Nothing accumulates
silently.

Usage::

    python3 scripts/learn.py \\
        --root /path/to/config \\
        --topic "LocKey 命名规则" \\
        --body "所有 LocKey 都是 ITEM_<id>_NAME 格式" \\
        --evidence "Item 表 5 条已有数据全符合此模式" \\
        --apply-when "加新道具时,LocKey 直接按 ITEM_<新id>_NAME 生成"

Or, for non-ASCII content on Windows, use ``--config FILE`` (UTF-8 JSON
with the same field names as snake_case dest keys).

The memory directory is shared between read (``inspect_config_tables.py``)
and write (this script). Where it lands is decided by ``_memory_locator``:

  1. ``--memory-root <path>`` honoured first (explicit override).
  2. Otherwise walk up to 3 ancestors from ``--root`` and reuse the first
     existing ``.ai-config-table/`` found — so a teammate's入档 stays in
     the same dir even when they pass different ``--root`` values.
  3. Only when no existing memory is found, create one at
     ``<root>/.ai-config-table/`` (first-time入档).

The directory is opt-in per project; the agent must explicitly invoke
this script (after user approval) for any content to land there.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

# Sibling modules — rely on the script's directory being on sys.path[0].
from _config_loader import check_paths, load_config_file, merge_into_args
from _memory_locator import add_memory_root_arg, locate_for_read, locate_for_write


MEMORY_README = """# .ai-config-table/ —— AI 项目记忆

这个目录装 **ai-config-table skill 在本项目上的累积经验**。AI 每次 inspect 会自动读这里,开工前把规律应用到当前任务。

- `项目规律.md` —— AI 学到的项目特有规则(命名约定 / 跨表引用 / ID 段语义 / 隐藏列约定 等)。每条都是用户**明示同意**后入档,绝不静默累积。
- `项目档案.md`(可选) —— 项目级长期约定(路径锚点 / 多版本布局 / 写表入口)。AI 跟用户共编,inspect 自动读取。
- 你可以**直接编辑、删除、重组**这里的文件,下次 inspect 会读最新版。
- 要不要 commit 进项目仓库由你定:commit 后团队共享;不 commit 就是个人本地经验。

兼容老项目:目录里若已有 `learned-patterns.md` / `profile.md` / `README.md`(老英文名)也照常读取,新增内容写到老文件里 —— 不会出现新旧两份并存。
"""

LEARNED_HEADER = """# 项目规律(由 ai-config-table skill 累积)

> 每条规律都是用户明示同意后入档。
> 修改 / 删除 / 重组直接编辑此文件,AI 下次会读最新版本。

"""

# 优先使用的中文文件名 + 老英文兼容名。读 / 写都先看老文件,有就用老的(不分裂);
# 没有老的、第一次入档时用新中文名。
PATTERNS_FILENAME_NEW = "项目规律.md"
PATTERNS_FILENAME_LEGACY = "learned-patterns.md"
README_FILENAME_NEW = "说明.md"
README_FILENAME_LEGACY = "README.md"


def resolve_patterns_path(memory_dir: Path) -> Path:
    """老英文文件存在就继续往里写;否则首次入档用中文名。"""
    legacy = memory_dir / PATTERNS_FILENAME_LEGACY
    if legacy.exists():
        return legacy
    return memory_dir / PATTERNS_FILENAME_NEW


def resolve_readme_path(memory_dir: Path) -> Path:
    legacy = memory_dir / README_FILENAME_LEGACY
    if legacy.exists():
        return legacy
    return memory_dir / README_FILENAME_NEW


def ensure_memory_dir(memory_dir: Path) -> None:
    memory_dir.mkdir(parents=True, exist_ok=True)
    readme = resolve_readme_path(memory_dir)
    if not readme.exists():
        readme.write_text(MEMORY_README, encoding="utf-8")
    patterns = resolve_patterns_path(memory_dir)
    if not patterns.exists():
        patterns.write_text(LEARNED_HEADER, encoding="utf-8")


def render_pattern(topic: str, body: str, evidence: str | None, apply_when: str | None) -> str:
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    parts = [f"## {stamp} — {topic}", "", f"**规律**: {body}", ""]
    if evidence:
        parts += [f"**证据**: {evidence}", ""]
    if apply_when:
        parts += [f"**何时应用**: {apply_when}", ""]
    parts.append("---")
    parts.append("")
    return "\n".join(parts)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Append a learned pattern to a project's .ai-config-table/ memory.")
    parser.add_argument(
        "--root", type=Path, default=None,
        help="Config root (the project's config folder). The pattern is saved to "
             "<root>/.ai-config-table/learned-patterns.md. (Required, but can also be in --config.)",
    )
    parser.add_argument("--topic", type=str, default=None, help="Short title for the pattern.")
    parser.add_argument("--body", type=str, default=None, help="The rule, in 1-2 sentences.")
    parser.add_argument("--evidence", type=str, default=None, help="Evidence backing the rule (optional but recommended).")
    parser.add_argument("--apply-when", type=str, default=None, help="When AI should apply this in future tasks (optional).")
    parser.add_argument(
        "--config", type=Path, default=None,
        help="Read all params from a UTF-8 JSON config file (use on Windows when "
             "paths contain non-ASCII characters).",
    )
    add_memory_root_arg(parser)
    args = parser.parse_args()
    cfg = load_config_file(args.config)
    merge_into_args(args, cfg, path_fields=("root", "memory_root"))
    check_paths(args, ("root", "config", "memory_root"))
    return args


def main() -> None:
    args = parse_args()
    for field in ("root", "topic", "body"):
        if getattr(args, field) is None:
            raise SystemExit(f"--{field} is required (pass it on the CLI or include it in --config).")
    if not args.root.exists():
        raise SystemExit(f"Root not found: {args.root}")

    # Tell the user *which* memory dir we're writing to and why — it's the most
    # common source of "my入档 disappeared" surprise (e.g. teammate wrote here,
    # I read from there).
    located = locate_for_read(args.root, memory_root=args.memory_root)
    memory_dir = locate_for_write(args.root, memory_root=args.memory_root)
    if args.memory_root is not None:
        sys.stderr.write(f"[learn] using --memory-root: {memory_dir}\n")
    elif located is not None:
        sys.stderr.write(
            f"[learn] reusing existing memory ({located[1]} parent(s) above --root): {memory_dir}\n"
        )
    else:
        sys.stderr.write(f"[learn] first-time入档, creating: {memory_dir}\n")

    ensure_memory_dir(memory_dir)
    patterns_path = resolve_patterns_path(memory_dir)

    block = render_pattern(args.topic, args.body, args.evidence, args.apply_when)
    with patterns_path.open("a", encoding="utf-8") as f:
        f.write(block)

    sys.stdout.write(
        "✅ 入档完成\n"
        f"  做了什么:在「项目规律」里追加 1 条 (topic: {args.topic})\n"
        f"  写到哪了:{patterns_path}\n"
        f"  下次效果:跑 inspect 时,这条规律会出现在 inventory 顶部的 Project Memory 段,AI 自动应用\n"
    )


if __name__ == "__main__":
    main()
