# ai-config-table-skill

> 🌍 中文版: [README.md](README.md)

A portable AI skill that lets your assistant (Claude Code, Codex, Cursor, or any agent that runs Python 3.8+) safely edit your **configuration tables** — Excel / CSV / TSV / JSON — without touching the original file until you say so.

No MCP, no plugins, no SaaS. Just a folder of Markdown + Python.

## What problem does this solve?

Game designers, PMs, and non-engineers often own large Excel / CSV configuration tables (item tables, level tables, reward tables, localization tables). Asking an AI to "just change row 10001's quality from 2 to 3" today is dangerous:

- The AI might overwrite your file in place and break something downstream.
- It might guess a column name wrong and silently corrupt a row.
- It might miss that a related table (localization, icons) also needs an entry.

This skill wraps the AI in a **scan → preview → make-a-copy → compare → user-confirms** loop. Your original file is never touched until you explicitly confirm. The AI does the typing; you do the deciding.

## Who is this for?

- **Game designers / PMs** who own config tables and currently fear letting an AI touch them.
- **Engineers** who want a reusable, audit-friendly pattern for AI-assisted config edits across projects.
- **Anyone** using Claude Code, Codex, Cursor, or another agent CLI on tabular config data.

You do **not** need to know Python, JSON, or the command line. The AI runs every command; you just talk to it in plain language.

## Install

Pick the line that matches your agent:

```bash
# Codex CLI
git clone https://github.com/1aita0v/ai-config-table-skill.git "${CODEX_HOME:-$HOME/.codex}/skills/ai-config-table"

# Claude Code (user-level — available in all projects)
git clone https://github.com/1aita0v/ai-config-table-skill.git ~/.claude/skills/ai-config-table

# Cursor / Continue / Aider / other
git clone https://github.com/1aita0v/ai-config-table-skill.git ~/ai-config-table-skill
# then add a line to your project rules file (.cursorrules, AGENTS.md, CLAUDE.md):
#   See ~/ai-config-table-skill/SKILL.md for config-table editing workflow.
```

That's it. Next time you talk to your agent about a config table, the skill activates automatically (the YAML `description` field at the top of `SKILL.md` covers the common trigger phrases).

**Requirements:** Python 3.8+. For `.xlsx` / `.xlsm` editing, `pip install openpyxl`. CSV / TSV / JSON work with the Python standard library alone.

## What a minimal interaction looks like

```
You:  Help me change item 10001's quality from 2 to 3 in ~/myproj/cfg/Item.xlsx

AI:   Found it. Item 10001 is "Sword", currently quality 2. I'll make a copy with
      just that one cell changed (highlighted yellow) — your original is untouched.
      Preview the change before I generate the copy?

You:  Yes

AI:   Preview: Item sheet, row 5 (the row starting with `10001 / Sword`),
      Quality column, 2 → 3. Nothing else changes. Generate the copy?

You:  Generate

AI:   Done: ~/myproj/cfg/Item_candidate.xlsx. Comparison vs. original shows only
      that one cell changed. Want me to overwrite Item.xlsx with this, or will
      you copy it over yourself?
```

## Updating

When the maintainer publishes a fix or improvement, pull it:

```bash
cd ~/.claude/skills/ai-config-table   # or wherever you installed it
git pull
```

Tagged releases (`git tag --list`) mark stable points. Use `git checkout v1.0` to pin.

## What's inside

- `SKILL.md` — the workflow the AI follows, including dialogue patterns and how to talk to non-engineers.
- `scripts/` — three small Python scripts the AI runs (scan / patch / compare).
- `references/` — templates and checklists the AI fills in.
- `examples/` — a generated sample workbook + a complete walkthrough.
- `agents/openai.yaml` — Codex / OpenAI-style skill metadata.

## License

MIT. See [LICENSE](LICENSE).

## Found a bug or want an improvement?

Open an issue at https://github.com/1aita0v/ai-config-table-skill/issues — include the file format, what you asked the AI to do, and what went wrong.
