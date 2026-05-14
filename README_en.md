# ai-config-table-skill

[![License: MIT](https://img.shields.io/github/license/1aita0v/ai-config-table-skill)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![Latest tag](https://img.shields.io/github/v/tag/1aita0v/ai-config-table-skill?label=release)](https://github.com/1aita0v/ai-config-table-skill/tags)

A portable skill that lets AI agents (Claude Code, Codex, Cursor, …) **safely edit Excel / CSV / TSV / JSON configuration tables**: the original file is never modified before the user explicitly confirms a candidate copy and its diff.

No MCP, no plugins, no SaaS — just Markdown plus a handful of Python scripts.

> 中文版本见 [README.md](README.md)。

---

- **Designers / PMs**: installation is a developer task. Once installed, talk to your AI agent in plain language about which row of which table to change; the agent will produce a candidate, show a preview, and wait for your approval before overwriting. See the dialogue samples in [`SKILL.md`](SKILL.md).
- **Developers / engineers**: read on.

## What problem this solves

Designers and non-engineers maintain large Excel / CSV configuration tables (items, levels, rewards, localization). Asking an AI to edit them directly has three common failure modes:

1. The AI overwrites the source file, breaking downstream builds.
2. The AI misidentifies a column and silently corrupts a row — discovered days later.
3. A related table (localization, icons) is missed, producing blanks or runtime asserts.
4. Temporary formulas remain in the sheet, then calculate incorrectly after rows / row-count settings expand.

This skill wraps every edit in a fixed **inspect → formula gate → preview → candidate → diff → user confirms** pipeline, making "AI does the typing, human decides" the default behavior — not something the prompt has to remind it of.

## Pipeline

```
inspect        →  formula gate      →  patch (dry-run)  →  patch          →  diff             →  validate_refs
scan tables       choose handling       preview cells       copy source,      compare source     cross-table FK
emit inventory    values or preserve    do not write        edit candidate,   vs candidate per   (orphan) check —
+ patch skeleton  verify results if kept                  mark edited yellow sheet              last guard before
                                                                                                  overwrite
```

Each step is an independent Python script with atomic failure (errors exit cleanly and never leave half-written outputs). The agent follows the `SKILL.md` workflow to chain them and pauses for user input at "generate candidate" and "overwrite source" decision points.

## Quickstart (5 minutes, local)

```bash
git clone https://github.com/1aita0v/ai-config-table-skill.git
cd ai-config-table-skill
pip install openpyxl

# Build a sample workbook (mimics a typical game config: multi-row header + loc + reward tables)
python3 examples/build_sample.py

# Run the full pipeline
python3 scripts/inspect_config_tables.py --root examples/sample.xlsx --format md --output inventory.md --patch-template patch.json
python3 scripts/patch_xlsx.py     --source examples/sample.xlsx --output examples/sample_candidate.xlsx --patch examples/sample-patch.json --dry-run
python3 scripts/patch_xlsx.py     --source examples/sample.xlsx --output examples/sample_candidate.xlsx --patch examples/sample-patch.json
python3 scripts/diff_config_tables.py --source examples/sample.xlsx --candidate examples/sample_candidate.xlsx --output diff.md
python3 scripts/validate_refs.py  --workbook examples/sample_candidate.xlsx
```

The annotated version with expected output and cleanup is in [`examples/walkthrough.md`](examples/walkthrough.md).

## Installing into your agent

Pick the line matching your agent CLI:

```bash
# Codex CLI
git clone https://github.com/1aita0v/ai-config-table-skill.git "${CODEX_HOME:-$HOME/.codex}/skills/ai-config-table"

# Claude Code (user-level — available in every project)
git clone https://github.com/1aita0v/ai-config-table-skill.git ~/.claude/skills/ai-config-table

# Cursor / Continue / Aider / other
git clone https://github.com/1aita0v/ai-config-table-skill.git ~/ai-config-table-skill
# Then add a line to your project rules file (.cursorrules / AGENTS.md / CLAUDE.md):
#   For config-table edits, follow the workflow in ~/ai-config-table-skill/SKILL.md.
```

The agent activates the skill automatically once installed — the YAML trigger phrases cover common English and Chinese expressions (`change config table`, `add a row`, `AI配表`, `改配置表`, …).

## What's inside

| Path | Purpose |
|---|---|
| [`SKILL.md`](SKILL.md) | The workflow the AI follows — decision points, dialogue samples, change-set tiering, platform notes, project memory |
| [`scripts/inspect_config_tables.py`](scripts/inspect_config_tables.py) | Scans a config directory; emits `inventory.md` and a pre-filled `patch.json` skeleton |
| [`scripts/patch_xlsx.py`](scripts/patch_xlsx.py) | Copies source to candidate, applies the patch JSON, highlights edited cells; supports `--dry-run` |
| [`scripts/diff_config_tables.py`](scripts/diff_config_tables.py) | Compares source and candidate per sheet, surfacing value diffs and formula changes; `--compare-formula-results` compares cached formula results after recalculation |
| [`scripts/validate_refs.py`](scripts/validate_refs.py) | Cross-table FK (orphan) check — auto-detects references like `Item.LocKey → LocText.LocKey` |
| [`scripts/find_table.py`](scripts/find_table.py) | Keyword search across sheets and fields in an inventory (for vague user descriptions) |
| [`scripts/learn.py`](scripts/learn.py) | Persists user-confirmed field meanings and conventions into `<config-root>/.ai-config-table/` project memory |
| [`references/`](references/) | Templates and checklists the AI consults internally — patch JSON format, field-meaning evidence sources, RPG config patterns, pre-release checklist, etc. |
| [`examples/walkthrough.md`](examples/walkthrough.md) | The full annotated run on the generated sample workbook |
| [`agents/openai.yaml`](agents/openai.yaml) | Codex / OpenAI-style agent metadata (skill activation config) |

## Compatibility

- **Python**: 3.8+
- **OS**: macOS / Linux / Windows
- **xlsx / xlsm editing**: `pip install openpyxl`
- **CSV / TSV / JSON**: standard library only

On Windows the default code page is cp936/GBK; passing non-ASCII paths to Python on the command line often mangles them (`C:\TR\????\X.xlsx`). All scripts accept `--config FILE` to read parameters from a UTF-8 JSON file and bypass argv encoding entirely; they also detect `?` in paths and print a clear remediation message. Full details in the "Windows + non-ASCII paths" section of `SKILL.md`.

## Versions

Use `git tag --list` to browse history and `git checkout v1.x` to pin. Notable milestones in the current series:

- **v2.x** — fuzzy input handling, 4-tier change-set granularity, `find_table` keyword search
- **v1.7** — project memory under `<config-root>/.ai-config-table/`
- **v1.5+** — full Windows + non-ASCII path support
- **v1.4** — note column, pinned dependency versions, write-path fallback

Per-version details live in the corresponding commit messages.

## Updating

```bash
cd ~/.claude/skills/ai-config-table   # or wherever you installed it
git pull
```

## License

MIT. See [LICENSE](LICENSE).

## Feedback

Bug reports and feature requests: [GitHub Issues](https://github.com/1aita0v/ai-config-table-skill/issues). Please include file format, the instruction given to the AI, and the gap between actual and expected behavior.
