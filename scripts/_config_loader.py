"""Shared helpers for letting CLI scripts accept a UTF-8 JSON config file.

Why this exists
---------------

On Windows the default code page is usually cp936/GBK, not UTF-8. When an
agent (Codex / Claude Code / etc.) spawns a Python subprocess and passes
a path like ``C:\\TR\\配置表\\装备\\X.xlsx`` as a command-line argument,
the OS/shell layer between the agent and Python silently encodes the
argv with cp936. If anything along the way decodes with strict ASCII,
the Chinese characters are replaced with ``?`` — by the time Python
reads ``sys.argv`` the original bytes are lost.

There's no way to recover the original characters from inside Python
once that has happened. The robust workaround is to keep non-ASCII
strings out of argv entirely:

  1. The agent writes a UTF-8 JSON config file to an ASCII-only path
     (typically the skill's own directory, ``/tmp``, or ``C:\\Temp``).
  2. The agent invokes the script with ``--config /ascii/path/config.json``
     (the only non-ASCII strings are inside the JSON, never on argv).
  3. The script reads the JSON with explicit UTF-8 decoding,
     reconstructs the right argparse fields, and proceeds normally.

This module bundles helpers used by all four bundled scripts.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Iterable


def assert_path_not_mangled(path: Any, label: str) -> None:
    """Detect the cp936/argv mangling failure mode and surface a clear error.

    The diagnostic ``?`` character can never legally appear in a Windows
    filename and almost never in a real Unix filename. So if we see one,
    we're almost certainly looking at a botched argv decode.
    """
    if path is None:
        return
    text = str(path)
    if "?" not in text:
        return
    raise SystemExit(
        f"--{label} contains the character '?': {text}\n"
        "\n"
        "This almost always means a non-ASCII path got corrupted while being\n"
        "passed to Python on argv (Windows + cp936 codepage is the usual culprit;\n"
        "the original characters cannot be recovered from inside Python).\n"
        "\n"
        "Fix (pick one):\n"
        "  1. Use --config FILE (preferred). Put a UTF-8 JSON file at an\n"
        "     ASCII-only path (e.g. C:\\Temp\\config.json) containing the real\n"
        "     paths, then pass --config C:\\Temp\\config.json. Paths inside the\n"
        "     JSON travel as Unicode and never touch the shell's codepage.\n"
        "  2. Run `chcp 65001` in cmd before launching the agent.\n"
        "  3. Set the environment variable PYTHONUTF8=1 before running Python.\n"
        "  4. Temporarily rename the config directory so its name is ASCII-only."
    )


def load_config_file(path: Path | None) -> dict[str, Any]:
    """Load a UTF-8 JSON config file. utf-8-sig tolerates a Windows BOM."""
    if path is None:
        return {}
    assert_path_not_mangled(path, "config")
    if not path.exists():
        raise SystemExit(f"--config file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def merge_into_args(
    args: Any,
    config: dict[str, Any],
    path_fields: Iterable[str],
    list_fields: Iterable[str] = (),
) -> None:
    """Overlay config-file values onto an argparse Namespace, in place.

    - Keys with hyphens (e.g. "field-row") map to argparse dest names
      with underscores ("field_row").
    - String fields named in ``path_fields`` are wrapped in pathlib.Path.
    - Fields in ``list_fields`` accept either JSON arrays or
      comma-separated strings; either way they become lists of the right
      element type (best-effort).
    - Unknown keys (not in the argparse Namespace) are ignored.
    """
    path_set = set(path_fields)
    list_set = set(list_fields)
    for raw_key, value in config.items():
        dest = raw_key.replace("-", "_")
        if dest == "config":
            continue
        if not hasattr(args, dest):
            sys.stderr.write(f"[config] ignoring unknown key: {raw_key}\n")
            continue
        if value is None:
            continue
        if dest in path_set:
            setattr(args, dest, Path(value))
        elif dest in list_set:
            if isinstance(value, list):
                setattr(args, dest, list(value))
            else:
                parts = [p.strip() for p in str(value).split(",") if p.strip()]
                setattr(args, dest, parts)
        else:
            setattr(args, dest, value)


def check_paths(args: Any, fields: Iterable[str]) -> None:
    """Run assert_path_not_mangled on every path-bearing arg."""
    for field in fields:
        value = getattr(args, field, None)
        if value is None:
            continue
        assert_path_not_mangled(value, field.replace("_", "-"))
