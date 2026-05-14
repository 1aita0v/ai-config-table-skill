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


MEMORY_README = """# .ai-config-table/

这个目录是 **ai-config-table skill 在本项目上的累积学习**。

- `learned-patterns.md` — AI 跑配表任务时观察到的稳定规律(命名约定 / 跨表引用 / ID 段语义 等)。每条都是用户**明示同意**后入档的,绝不静默累积。
- 你可以**直接编辑、删除、重组**这里的文件。
- 决定要不要 commit 进项目仓库由你定:commit 后团队共享;不 commit 就是个人本地经验。

下次 AI 跑 inspect,会自动把这里的内容附在 inventory 末尾,开工前先读、再动手。
"""

LEARNED_HEADER = """# Learned Patterns

> AI 在本项目上累积的规律。每条入档都是用户明示同意后写入。
> 修改 / 删除 / 重组直接编辑此文件,AI 下次会读最新版本。

"""


def ensure_memory_dir(memory_dir: Path) -> None:
    memory_dir.mkdir(parents=True, exist_ok=True)
    readme = memory_dir / "README.md"
    if not readme.exists():
        readme.write_text(MEMORY_README, encoding="utf-8")
    patterns = memory_dir / "learned-patterns.md"
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
    patterns_path = memory_dir / "learned-patterns.md"

    block = render_pattern(args.topic, args.body, args.evidence, args.apply_when)
    with patterns_path.open("a", encoding="utf-8") as f:
        f.write(block)

    sys.stdout.write(
        f"Appended pattern to {patterns_path}\n"
        f"  Topic: {args.topic}\n"
        f"  This memory will surface in inspect's inventory output on the next run.\n"
    )


if __name__ == "__main__":
    main()
