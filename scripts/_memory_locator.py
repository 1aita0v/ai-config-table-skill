"""Locate .ai-config-table/ memory directories near a given root.

Used by inspect_config_tables.py and learn.py so both agree on where memory
lives. Without this, one script writes to <root>/.ai-config-table/ while the
other reads from a parent — agents on the same project never converge on the
same memory.

Lookup rules (used by both read and write):

1. ``--memory-root <path>`` (explicit override) — accept both forms:
   ``<path>/.ai-config-table`` or ``<path>`` already pointing inside one.
2. Walk up from ``<root>`` at most 3 ancestors and return the first
   ``.ai-config-table/`` found. Handles the standard case "config files live
   in a subdir of the engineering repo".
3. Reads: return ``None`` when neither is found.
4. Writes: when neither is found, default to ``<root>/.ai-config-table`` —
   that becomes the first-time入档 location.
"""

from __future__ import annotations

import argparse
from pathlib import Path

MAX_LEVELS = 3


def _resolve_start(root: Path) -> Path:
    """Pick the directory to start walking up from. Works on non-existent paths."""
    resolved = root.resolve() if root.exists() else root
    return resolved.parent if resolved.is_file() else resolved


def _explicit_dir(memory_root: Path) -> Path:
    """Normalize an explicit --memory-root: append .ai-config-table/ unless
    the user already pointed at one."""
    if memory_root.name == ".ai-config-table":
        return memory_root
    return memory_root / ".ai-config-table"


def locate_for_read(root: Path, memory_root: Path | None = None) -> tuple[Path, int] | None:
    """Find an existing ``.ai-config-table/`` near ``root``.

    Returns ``(memory_dir, levels_up)``:
      - ``levels_up == 0``  → memory dir sits at root itself
      - ``levels_up == N``  → memory dir is N ancestor directories above root
      - ``levels_up == -1`` → an explicit ``--memory-root`` was honoured
    Returns ``None`` when no memory dir is found within ``MAX_LEVELS``.
    """
    if memory_root is not None:
        explicit = _explicit_dir(memory_root)
        return (explicit, -1) if explicit.is_dir() else None

    current = _resolve_start(root)
    for level in range(MAX_LEVELS + 1):
        candidate = current / ".ai-config-table"
        if candidate.is_dir():
            return (candidate, level)
        parent = current.parent
        if parent == current:  # reached filesystem root
            break
        current = parent
    return None


def locate_for_write(root: Path, memory_root: Path | None = None) -> Path:
    """Decide where to write memory.

    1. ``--memory-root <path>``: write to ``<path>/.ai-config-table`` (created
       on first use).
    2. Existing memory found via upward search: reuse it so writes converge
       with reads.
    3. Default: ``<root>/.ai-config-table`` — first-time入档 lands here.
    """
    if memory_root is not None:
        return _explicit_dir(memory_root)
    found = locate_for_read(root)
    if found is not None:
        return found[0]
    return _resolve_start(root) / ".ai-config-table"


def add_memory_root_arg(parser: argparse.ArgumentParser) -> None:
    """Register ``--memory-root`` on a parser with consistent help text."""
    parser.add_argument(
        "--memory-root",
        type=Path,
        default=None,
        help="Explicit directory holding (or that should hold) .ai-config-table/. "
             "Use when the engineering repo is a separate directory tree from the "
             "config source (e.g. external SVN config mirror + independent git "
             "engineering repo). If omitted, scripts walk up to 3 parents from "
             "--root looking for an existing .ai-config-table/.",
    )
