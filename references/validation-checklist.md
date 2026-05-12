# Validation Checklist

Use this after producing a candidate config table.

## Structural Checks

- Candidate file exists and opens/parses.
- File type is preserved unless conversion is intentional.
- Workbook sheet names are unchanged unless the spec says otherwise.
- Header rows are unchanged unless the spec says otherwise.
- Formula cells are unchanged unless the spec says otherwise.
- Hidden sheets, merged cells, comments, freeze panes, and data validation are not intentionally relied on unless checked.

## openpyxl Re-save Caveats

`patch_xlsx.py` uses openpyxl, which can silently drop or alter:

- **Data validation dropdowns** in certain forms (long enum lists, cross-sheet references).
- **Some conditional formatting** rules, especially complex ones authored in Excel.
- **Embedded charts** created in old Excel versions.
- **Printer settings**, page setup, custom views.
- **Cell styles** beyond the basic font / fill / border / number-format set.

These won't show up in `diff_config_tables.py` (it compares cell values). If your project relies on any of the above, open the candidate in Excel / WPS once before writeback and compare visually, or use a project-native exporter that goes through Excel's own object model.

## Data Checks

- Every planned row/key exists in the candidate.
- Every planned field has the expected value.
- No unintended changes appear in the diff.
- Primary keys are non-empty and unique.
- Required fields are non-empty.
- Types and list separators match nearby examples.
- New IDs do not collide with existing IDs.

## Cross-Table Checks

Check only dependencies that the task can touch:

- Localization/name/description keys.
- Prompt/error text keys.
- Resource/icon/audio/effect references.
- Item/reward/drop references.
- Unlock/condition references.
- Entry/jump/guide references.
- Battle/event/effect references.
- Enum/dictionary values.
- Generated export references.

For each dependency, mark one of:

- `pass`: checked and present.
- `not applicable`: explain why the task does not touch it.
- `needs decision`: human/design decision needed.
- `missing`: fix before writeback.

## Source Writeback Gate

Writeback is allowed only when:

- User explicitly asked for writeback.
- Candidate validation passed or exceptions are accepted.
- Diff is reviewed.
- Source lock/version/conflict policy is satisfied.
- Backup or rollback path exists.

## Report Shape

```markdown
# Config Validation Report

## Summary

- Result:
- Source:
- Candidate:
- Diff:

## Passed

| Check | Evidence |
|---|---|
|  |  |

## Needs Decision

| Item | Reason | Options |
|---|---|---|
|  |  |  |

## Missing Or Failed

| Item | Evidence | Fix |
|---|---|---|
|  |  |  |

## Writeback Readiness

- Ready: yes/no
- Blockers:
```
