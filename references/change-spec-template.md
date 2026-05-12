# AI Config Change Spec Template

Use this before medium/high risk AI配表 work.

```markdown
# {Task} Config Spec

## Goal

- User request:
- Expected game/product behavior:
- Non-goals:

## Source And Output

- Source type: local / export / cloud sheet / platform API / project tool / mixed
- Source project/root:
- Target workbook/sheet:
- Candidate output:
- Writeback policy: candidate only / writeback after confirmation / no writeback

## Current Evidence

- Inventory/profile path:
- Sample rows inspected:
- Similar existing rows:
- ID allocation evidence:
- Relevant docs:

## Planned Changes

| Action | Workbook | Sheet | Key/Row | Fields | Reason |
|---|---|---|---|---|---|
| add/update/delete |  |  |  |  |  |

## Cross-Table Impact

| Dependency | Needed? | Evidence | Action |
|---|---|---|---|
| Localization | yes/no/unknown |  |  |
| Prompt/Error text | yes/no/unknown |  |  |
| Resource/Icon/Audio/Effect | yes/no/unknown |  |  |
| Item/Reward | yes/no/unknown |  |  |
| Condition/Unlock | yes/no/unknown |  |  |
| Guide/Jump/Entry | yes/no/unknown |  |  |
| Enum/Dictionary | yes/no/unknown |  |  |

## Patch Plan

- Patch file:
- Script/tool:
- Tables touched:
- Fields intentionally changed:
- Fields that must remain unchanged:

## Acceptance Criteria

- [ ] Target rows/fields match the requested behavior.
- [ ] Primary keys are unique and follow project allocation rules.
- [ ] Cross-table references exist or are marked not applicable with evidence.
- [ ] Headers, formulas, styles, and unrelated sheets are preserved.
- [ ] Candidate diff only contains intended changes.
- [ ] Project parser/exporter can read the candidate, if available.
- [ ] Human decision items are listed.
```
