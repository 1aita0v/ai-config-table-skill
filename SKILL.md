---
name: ai-config-table
description: >-
  Portable AI workflow for editing any project's configuration tables safely.
  Use whenever a user asks to inspect, document, change, generate, patch,
  validate, or review config data — local Excel/CSV/TSV/JSON files, exported
  workbooks, cloud sheets, or platform table APIs. Triggers include "AI配表",
  "读配置表", "改配置表", "加一行/新增一条", "批量改", "配表复核",
  "配表知识库", "跨表引用校验", "use this project's config tables". Works under
  Claude Code, Codex, Cursor, or any agent that can run Python 3.8+ and read
  this directory.
version: 4
---

# AI Config Table

## Who you'll be talking to (agent: read this first)

The user is most likely a **game designer, PM, or non-engineer**. Assume they:

- Cannot run Python commands themselves.
- Don't know what "primary key", "FK", "header row", "schema", "dry-run", or "JSON" mean by default.
- Just want a row changed, a row added, a value tweaked — and they want it to **not break the game/product**.

You (the agent) run all commands. The user only confirms decisions in plain language. Never paste a command and ask the user to run it. Never expect them to read a `.json` patch file. Translate everything.

If you find yourself about to say "header_row=2" or "edit the patch JSON", stop and rephrase — see *Talking to non-engineers* below.

## What this skill does (in plain words)

A safe five-step loop for changing someone else's config tables:

1. **Ask** the user where the table is and what's in it — never guess.
2. **Look** at the table read-only and write down what's there.
3. **Plan** the change in a short note — only needed for bigger changes.
4. **Make a copy** with the change applied (never touch the original).
5. **Compare** the copy to the original and let the user check before anything is "really saved".

> Rule the user can hold you to: **the original file is never touched until they say "yes, overwrite it"**.

## When the user first comes to you

Before you read or change anything, you need three things. Ask in plain words, not jargon:

> Before I touch anything, three quick questions:
> 1. Where are the tables? — a folder on your computer, a zip someone sent you, a cloud sheet link, or some admin panel?
> 2. What kind of files? — Excel (`.xlsx`), CSV, JSON, or a mix?
> 3. The top rows of the sheet — is the very first row the column names, or are there 2-4 rows on top (like a Chinese name row, an English-name row, a type row, a comment row)? If you're not sure, just point me at the folder and I'll guess and check with you.

If the user can't reach any source, write a `no-data-source-report.md` (see `references/no-data-source-report.md`) and **stop**. Do not invent table names, IDs, or rules.

## Talking to non-engineers (agent glossary)

Replace internal terms with the right-hand phrasing when talking to the user. Keep the internal terms when reading docs or writing patches.

| Internal term | What you say to the user |
|---|---|
| `field_row` / `header_row` | "the row that has the column names" or "row N is the column-name row" |
| `meta_rows` | "the extra label rows on top (Chinese name / type / comment etc.)" |
| `data_start_row` | "the first row of real data" |
| primary key / `key_field` | "the unique ID column for this table (the one no two rows share)" |
| foreign key / cross-table reference / FK | "where this table points at another table" e.g. "the ItemID here matches an entry in the Item table" |
| schema | "table structure" or "what columns this table has" |
| dry-run | "let me preview the change without saving anything yet" |
| patch JSON | "the change list I'm building for you" — never show the raw JSON unless they ask |
| candidate file | "a copy of your table with the changes applied — your original is untouched" |
| writeback | "overwrite your original file with the new version" |
| diff | "side-by-side comparison" or "change list" |
| inspect / inventory | "a quick scan / list of what's in your files" |

When you must say a number ("row 5", "column D"), always pair it with what the user can see: "row 5 — the one starting with `10001 / Sword`".

## Sample dialogues (concrete patterns)

These show the *shape* of a good conversation. Adapt wording to the user's language.

### Dialogue 1 — User points at a folder

> **User**: 帮我看下我配置表里 Item 表的物品 10001 是什么
>
> **You**: 好,你的配置表在哪儿?给我一个文件夹路径,或者直接把 Excel 文件拖给我也行。
>
> **User**: `~/myproj/cfg/`
>
> **You**: *(runs `inspect_config_tables.py` on that folder, reads the result silently)* 找到了。`Item.xlsx` 这个表,前 4 行是表头(中文名 / 英文字段 / 类型 / 备注),第 5 行开始是数据。10001 这一行是:Sword(剑),描述 "A sword.",图标 `icon_sword`,品质 2。要改它的什么字段?

### Dialogue 2 — User wants to change one value

> **User**: 把 10001 的品质改成 3
>
> **You**: 收到。我会:
> - 不动你的原表 `Item.xlsx`
> - 生成一个改后的副本 `Item_candidate.xlsx`,只改 10001 这一行的品质,从 2 → 3
> - 改动的格子会标黄方便你检查
>
> 这样可以吗?(我先预览给你看,确认无误再实际生成副本)
>
> **User**: 行
>
> **You**: *(dry-run, shows the planned change in plain language)* 预览:Item 表第 5 行,品质列(第 5 列),`2` → `3`。其他都不动。生成副本?
>
> **User**: 生成
>
> **You**: *(runs patch, then diff)* 已生成 `~/myproj/cfg/Item_candidate.xlsx`。对比下来只动了这一格,其他完全一致。你打开看一下,如果 OK 我可以帮你把它覆盖回原表(`Item.xlsx`),或者你自己拖过去也行。

### Dialogue 3 — User wants to add new rows (cross-table risk)

> **User**: 帮我加 5 个新道具进 Item 表,ID 从 10020 开始
>
> **You**: 加 5 个新道具是中等复杂度的事 — 因为新道具通常还要在「文本表」(给玩家看的中文名)和「图标 / 资源表」里也有对应条目,不然游戏里可能显示成空白或者报错。我先核对几件事:
> 1. 你这 5 个道具的中文名、描述、图标分别是什么?
> 2. ID 10020-10024 这段还没被占用吧?(我先扫一遍确认)
> 3. 文本表(LocText 这种)和图标列表里要不要我一起加?
>
> 你先告诉我前两个,第 3 个我扫完就有答案了。

### Dialogue 4 — User doesn't know the answer to a structure question

> **User**: 不知道,你看着办
>
> **You**: 好,我先自己看一遍,5 秒。*(runs inspect)* 看完了。你的 Item 表第 2 行是英文字段名(ItemID / Name / Desc / Icon / Quality),第 1 行是中文(物品ID / 名称 / 描述 / 图标 / 品质),第 3 行是类型,数据从第 5 行开始。这种 4 行表头很常见,我按这个理解处理。
>
> 唯一编号字段是 `ItemID`(物品ID 那一列),我会用它来定位你要改的行。有问题随时打断我。

### Dialogue 5 — User asks for something risky without realizing

> **User**: 直接帮我把改完的文件覆盖回去就行,别给我看什么副本了,麻烦
>
> **You**: 理解你想省事。但配置表这种东西改错了通常很难发现 — 等到游戏里出 bug 才发现就晚了。我建议这样:
> - 我还是先生成副本(自动的,你不用做什么)
> - 我给你一句话总结改了什么,你看一眼,说"OK"
> - 我再覆盖回原表
>
> 整个过程多 30 秒,但能避免改错。可以吗?(如果你坚持直接覆盖,我也照办,但我会先备份原表到 `Item_backup_YYYYMMDD.xlsx`。)

## If your sandbox refuses to overwrite the source — don't bypass, hand off

Many agent runtimes (Codex sandbox, Claude Code restricted mode, Cursor) will refuse to **overwrite the user's original config file** even when the user explicitly asked. This is normal and is the runtime protecting the user. **Do not** try to:

- Re-run with `sudo` or elevated permissions.
- Write to a different path that you then ask the shell to `mv` over the source.
- Pipe through `cat > source.xlsx` to dodge the file-write check.
- Disable safety flags, run with `--dangerously-*` style options, or ask the user to.

Instead, **tell the user where the candidate file is and let them do the copy themselves**:

> 我已经把改好的版本生成到这里:
>
> `~/myproj/cfg/Item_candidate.xlsx`
>
> 不过我这边的运行环境不允许我直接覆盖你的原文件 `Item.xlsx`,这是默认的安全保护,正常的。请你手动操作一下:
>
> 1. 关掉 Excel(如果它正开着 `Item.xlsx`)
> 2. 把 `Item.xlsx` 重命名为 `Item_backup.xlsx`(保险起见)
> 3. 把 `Item_candidate.xlsx` 改名为 `Item.xlsx`
>
> 三步,30 秒。完成后告诉我一声,我可以再扫一遍确认它和我们刚才看到的副本一致。

This is a real recurring frustration. Handing off cleanly is the right move; the candidate file is the deliverable, the user closes the loop.

## Task-size routing

Don't run the full workflow for trivial questions.

| Task | Steps to run |
|---|---|
| Look up one field's meaning | inspect → answer (no spec) |
| Single-row update, no cross-table impact | inspect → patch (preview + apply) → compare |
| Add 1-5 rows | inspect → mini-spec → patch → compare → quick cross-table check |
| 10+ rows / new IDs / cross-table refs / formulas / structural changes | full 7-step workflow below |

## Full workflow (medium / high-risk tasks)

### 1. Discover

Build an inventory before interpreting business meaning. You run these — never ask the user to.

```bash
python3 scripts/inspect_config_tables.py --root /path/to/config --output inventory.json --format json
# or, for projects with 2+ header rows:
python3 scripts/inspect_config_tables.py --root /path/to/config --field-row 2 --meta-rows 1,3 --output inventory.md --format md
```

For cloud / platform sources: list workbooks, fetch headers + 3-5 sample rows per relevant sheet, export read-only copies if the platform supports it. Record the source, timestamp, and exact tool / query used.

### 2. Build project profile

Fill `references/project-profile-template.md`. Cover:

- Source of truth + access method.
- Workbook / sheet naming, header rows, data start row.
- Unique-ID column and how new IDs are allocated.
- Cross-table reference patterns (which tables point at which).
- Enum / dictionary tables.
- Localization, prompt, resource, item, reward, condition tables.
- Generated vs source-of-truth boundary.

For repeated work on the same project, follow `references/config-reference-playbook.md` to build a `config-reference/` knowledge layer.

### 3. Confirm task and risk

Restate to the user in plain language:

- Which file / sheet / range you'll touch.
- Which rows you'll add / change / remove.
- Which other tables might be affected.
- Whether you'll just produce a copy, or also overwrite the original.
- Risk: low / medium / high.

High risk = structure changes, new fields, cross-table references, formulas, new ID allocation, enum changes, generated exports, or 10+ data rows.

### 4. Write spec

For medium / high risk changes, fill `references/change-spec-template.md` before changing data. Show the user a one-paragraph summary; keep the full spec for your own bookkeeping.

### 5. Produce candidate

Use the project's own tools first (a `validate.py`, an export script, etc.) if they exist. Otherwise:

```bash
python3 scripts/patch_xlsx.py --source table.xlsx --output table_candidate.xlsx --patch changes.json
```

Never overwrite the source. Keep source and candidate side by side, or write to a task output folder.

### 6. Validate

```bash
python3 scripts/diff_config_tables.py --source table.xlsx --candidate table_candidate.xlsx --output diff.md
```

Then go through `references/validation-checklist.md`. Pay attention to the openpyxl re-save caveats listed there (data validation, conditional formatting, embedded charts may not round-trip perfectly).

### 7. Deliver

Tell the user:

- Where the candidate file is (absolute path).
- One-paragraph summary of what changed.
- Anything that needs the user's decision before going further.
- Whether you can overwrite the source for them, or whether they need to copy the candidate over manually (see *If your sandbox refuses to overwrite* above).

## Quick reference (the three commands you'll actually run)

```bash
# A. Scan a folder of config files
python3 scripts/inspect_config_tables.py --root /path/to/config --format md --output inventory.md

# B. Preview a change, then produce a candidate
python3 scripts/patch_xlsx.py --source table.xlsx --output table_candidate.xlsx --patch changes.json --dry-run
python3 scripts/patch_xlsx.py --source table.xlsx --output table_candidate.xlsx --patch changes.json

# C. Compare source vs candidate
python3 scripts/diff_config_tables.py --source table.xlsx --candidate table_candidate.xlsx --output diff.md
```

Worked example with sample data: `examples/walkthrough.md`.

## Operating principles

- **Source tables are read-only by default.** Candidate copies first, overwrite only after explicit user confirmation.
- **No invention.** If you don't know a field, ID, or reference, ask or mark unknown.
- **Project-native tools beat bundled scripts.** If the project has its own `validate`, `build`, `publish`, `lint`, `export` scripts, use them.
- **Multi-row headers are normal.** Many game / product configs have 2-4 header rows (Chinese name / English field / type / comment). Both `inspect` and `patch` accept `--field-row` and `--meta-rows`.
- **Encoding fallback.** CSV / JSON default to UTF-8; if decoding fails, the scripts retry with GBK and record which encoding worked.
- **Cross-check with an independent pass when possible.** The agent that produced a table should not be the only evidence that it's correct.
- **Sandbox refusals are not obstacles to work around.** They're the user's safety net — see the writeback handoff section above.

## Agent compatibility

This skill is plain Python + Markdown — no MCP, no plugins, no SaaS. Works wherever Python 3.8+ runs.

Common install paths:

- **Codex CLI**: `cp -R ai-config-table-skill "${CODEX_HOME:-$HOME/.codex}/skills/ai-config-table"`
- **Claude Code (user-level)**: `cp -R ai-config-table-skill ~/.claude/skills/ai-config-table`
- **Claude Code (project-level)**: `cp -R ai-config-table-skill .claude/skills/ai-config-table`
- **Cursor / Continue / Aider / other**: drop the folder anywhere visible to the agent, then add a one-line pointer in your project rules file (`.cursorrules`, `AGENTS.md`, `CLAUDE.md`) pointing at `ai-config-table-skill/SKILL.md`.

Required: Python 3.8+ and `openpyxl` (`pip install openpyxl`) for `.xlsx` / `.xlsm`. CSV / TSV / JSON are stdlib-only. The scripts print a clear install hint if `openpyxl` is missing.

## References

- `references/data-sources.md` — local / export / cloud / platform / project-tool routing.
- `references/no-data-source-report.md` — clean failure template when no source is reachable.
- `references/project-profile-template.md` — fillable per-project profile.
- `references/config-reference-playbook.md` — building a reusable per-project config knowledge layer.
- `references/change-spec-template.md` — spec template for medium / high-risk changes.
- `references/validation-checklist.md` — DoD + openpyxl re-save caveats.
- `references/patch-format.md` — JSON spec accepted by `patch_xlsx.py` (includes multi-row header fields).

## Bundled scripts

- `scripts/inspect_config_tables.py` — scan local config files into an inventory; supports multi-row headers and encoding fallback.
- `scripts/patch_xlsx.py` — copy a workbook and apply structured updates / appends; `--dry-run` previews without writing.
- `scripts/diff_config_tables.py` — compare source and candidate workbooks or directories; warns visibly on truncation.

## Examples

`examples/` ships a complete walkthrough:

- `build_sample.py` — generates a 3-sheet sample workbook with multi-row headers.
- `sample-patch.json` — updates one row, appends one row, in two sheets.
- `walkthrough.md` — three-command reproduction with expected output.

## Anti-patterns

- Editing source config tables before discovery and spec.
- Inferring business meaning only from ID ranges, filename fragments, or names.
- Updating a main table without checking localization / resource / reward / condition references.
- Treating generated client / server exports as the source of truth without checking project rules.
- Claiming validation passed without concrete file paths, row IDs, fields, and evidence.
- Assuming a single-row header when the workbook actually has 2-4 header rows.
- Showing the user raw JSON or shell commands and expecting them to read or run them.
- Working around the runtime's write protection to overwrite the source file — always hand the candidate file off to the user instead.
