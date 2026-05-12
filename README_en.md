# ai-config-table-skill

> 🌍 中文: [README.md](README.md)

A portable AI skill that lets your assistant (Claude Code, Codex, Cursor) safely edit your **configuration tables** — Excel / CSV / TSV / JSON — without touching the original file until you say so.

No MCP, no plugins, no SaaS. Just a folder of Markdown + Python.

---

## 👤 For designers / PMs: read this one section

**After install**, talk to your AI in plain language, e.g.:

> Change item 10001's quality to 3 in `~/myproj/cfg/Item.xlsx`

The AI will: **scan → preview → make a candidate copy (original untouched) → show a diff**. You say "overwrite" only after you're happy.

**You don't need to touch the command line or read JSON.** The install section below is for engineers; once installed, you just talk to your AI.

Worried the AI will break your file? The skill's core promise:
- Original is **never touched by default**; edits land in a candidate copy
- Any non-trivial change gets a dry-run preview first
- Formulas / comments / merged cells / VBA are usually preserved. **Data-validation dropdowns, complex conditional formatting, and embedded charts may not round-trip** — the AI will warn you and ask you to open the candidate in Excel / WPS to eyeball it before overwriting.

---

## What problem does this solve?

Game designers, PMs, and non-engineers often own large Excel / CSV configuration tables (items, levels, rewards, localization). Asking an AI to "just change row 10001's quality from 2 to 3" today is dangerous:

- The AI may overwrite your file in place
- It may guess a column name wrong and silently corrupt a row
- It may miss that a related table (localization, icons) also needs an entry

This skill wraps the AI in a **scan → preview → candidate → diff → user-confirms** loop. **AI does the typing; you do the deciding.**

## Who is this for?

- **Designers / PMs** who own config tables and currently fear letting an AI touch them
- **Engineers** who want a reusable, audit-friendly pattern for AI-assisted config edits
- **Anyone** using Claude Code, Codex, Cursor, or another agent CLI on tabular config data

## What a minimal interaction looks like

```
You:  Change item 10003's quality to 3 in ~/myproj/cfg/Item.xlsx

AI:   Found it. 10003 is "Potion", currently quality 2. I'll make a copy with
      just that one cell changed (highlighted yellow) — your original is untouched.
      Preview the change first?

You:  Yes

AI:   Preview: Item sheet, row 7 (the row starting `10003 / Potion`),
      Quality column, 2 → 3. Nothing else changes. Generate the candidate?

You:  Generate

AI:   Done: ~/myproj/cfg/Item_candidate.xlsx. The diff shows only that single
      cell changed. Want me to overwrite Item.xlsx, or copy it over yourself?
```

---

## Install (for engineers)

Pick the line that matches your agent:

```bash
# Codex CLI
git clone https://github.com/1aita0v/ai-config-table-skill.git "${CODEX_HOME:-$HOME/.codex}/skills/ai-config-table"

# Claude Code (user-level — available in all projects)
git clone https://github.com/1aita0v/ai-config-table-skill.git ~/.claude/skills/ai-config-table

# Cursor / Continue / Aider / other
git clone https://github.com/1aita0v/ai-config-table-skill.git ~/ai-config-table-skill
# add a line to your project rules file (.cursorrules, AGENTS.md, CLAUDE.md):
#   See ~/ai-config-table-skill/SKILL.md for config-table editing workflow.
```

That's it. Next time you talk to your agent about a config table, the skill activates automatically. The YAML triggers cover both English ("change config table", "use this project's config tables") and Chinese ("AI配表", "改配置表", "加一行") phrasings.

**Requirements:** Python 3.8+. For `.xlsx` / `.xlsm` editing, `pip install openpyxl`. CSV / TSV / JSON work with the standard library alone.

## Updating

```bash
cd ~/.claude/skills/ai-config-table   # or wherever you installed it
git pull
```

Tagged releases (`git tag --list`) mark stable points. Use `git checkout v1.2` to pin.

## What's inside

- `SKILL.md` — the workflow the AI follows, including dialogue patterns and how to talk to non-engineers
- `scripts/` — Python scripts the AI runs (scan / patch / diff / **cross-table reference validator**)
- `references/` — templates and checklists the AI uses internally (not user-facing forms)
- `examples/` — sample workbook builder + a complete walkthrough
- `agents/openai.yaml` — Codex / OpenAI-style skill metadata

## License

MIT. See [LICENSE](LICENSE).

## Found a bug / want an improvement?

Open an issue at https://github.com/1aita0v/ai-config-table-skill/issues — include the file format, what you asked the AI to do, and what went wrong.
