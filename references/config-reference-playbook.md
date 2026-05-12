# Config Reference Playbook

Use this when a project wants repeatable AI配表 instead of one-off table guessing.

## Core Idea

Do not make AI read every workbook from scratch each time. Build a routed config reference layer:

- A small index tells the agent what to read for each task.
- Each module covers one mental model or system slice.
- Source table data remains authoritative.
- The reference explains how to navigate and validate the source, not replace it.

This pattern keeps context small and makes AI behavior stable across projects.

## Recommended Structure

```text
config-reference/
├── README.md
├── 00-overview.md
├── 01-naming-id-terms.md
├── 02-core-systems.md
├── 03-support-tables.md
├── 04-field-index.md
├── 05-cross-table-constraints.md
├── 06-workflow-advice.md
└── 07-appendix-known-gaps.md
```

Use project-native names if preferred. Keep the same roles.

## README Index

The README should answer:

- What this reference is and what it is not.
- Where the actual source tables live.
- Which modules to read for common task types.
- Which constraints are mandatory before edits.
- Which docs or tables are authoritative when conflicts happen.

## Module Roles

### 00 Overview

Give the first mental model:

- Table ecosystem summary.
- Main table/support table/settlement table/presentation table roles.
- Directory or workbook-to-domain map.
- Minimal first-read set.

### 01 Naming, ID, Terms

Capture:

- ID formats and allocation rules.
- Business terms and field aliases.
- Localization key patterns.
- Enum naming format.

Never let agents infer business meaning only from ID ranges. Tell them which real fields decide category, profession, rarity, type, and quality.

### 02 Core Systems

Split by project domain:

- Battle/combat.
- Items/rewards.
- Economy/commercialization.
- Levels/dungeons.
- Characters/equipment.
- Events/live ops.

Each system module should list main tables, key fields, sample rows, and typical dependency tables.

### 03 Support Tables

Document tables that are not main systems but often decide whether work actually lands:

- Localization and prompt text.
- Conditions/unlocks.
- System entry, guide, jump.
- Resources, icons, audio, effects, windows.
- Items, rewards, shops, bags.
- Events/triggers.

### 04 Field Index

Create a quick field lookup for high-frequency tables:

| Table | Field | Meaning | References | Notes |
|---|---|---|---|---|
|  |  |  |  |  |

This is the fastest entry for "what does this field mean?" questions.

### 05 Cross-Table Constraints

List reference paths and hard constraints:

- Main table field -> dependency table key.
- Localization key -> sheet/key rule.
- Resource ID -> resource table.
- Reward ID -> item/reward table.
- Condition ID -> condition tree.
- Formula columns.
- High-risk primary/foreign keys.

Also list common missing dependencies grouped by text, access, settlement, and presentation.

### 06 Workflow Advice

Record project-specific habits that prevent bad AI配表:

- Before saying "not found", search all sheet headers.
- For category decisions, query business fields, not ID ranges.
- For player-facing text, check localization; for internal categories, check Desc/Type/Category.
- Before configuring a new type, blindly recreate 3-5 existing examples and diff against truth.
- For formula columns, use deterministic scripts and note recalculation needs.
- For cross-version backfill, compare schema fields before copying rows.

### 07 Appendix And Gaps

Keep:

- Representative examples.
- Enum dumps.
- Known blank rules.
- Questions requiring product/engineering decisions.

## Maintenance Rules

- The source tables are authoritative; the reference is a reading map.
- If a system-specific source doc exists, update it first, then update the AI-facing reference.
- Keep modules stable; prompt templates may link to them.
- Do not hide uncertainty. Mark "unknown" or "needs decision" with evidence.
- Include 3-5 real row examples for fragile rules.

## Minimum Viable Reference

If time is short, create only:

1. `README.md`: source, routing, hard constraints.
2. `00-overview.md`: table roles and first-read set.
3. `04-field-index.md`: high-frequency table fields.
4. `05-cross-table-constraints.md`: dependencies and write rules.

That is enough to make AI配表 much safer than raw table scanning.
