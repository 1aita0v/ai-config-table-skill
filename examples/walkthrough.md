# Walkthrough — three-command run

This walks through the full inspect → patch → diff loop on a generated sample workbook.

The sample mimics a typical game config: a multi-row header (CN display + EN field + type + comment) on the main table, plus a localization table and a reward table.

## 0. Setup (one time)

From the skill root directory:

```bash
pip install openpyxl
python3 examples/build_sample.py
```

This writes `examples/sample.xlsx` with three sheets:

| Sheet | Header rows | Data rows |
|---|---|---|
| Item | 4 (CN / EN / type / comment) | 5 |
| LocText | 2 (CN / EN field) | 5 |
| Reward | 1 | 3 |

## 1. Inspect

Run inspect with the field-row hint matching the Item sheet:

```bash
python3 scripts/inspect_config_tables.py \
  --root examples/sample.xlsx \
  --field-row 2 \
  --meta-rows 1,3,4 \
  --format md \
  --output examples/inventory.md
```

Open `examples/inventory.md`. You should see:

- Item sheet with `field_row=2 meta_rows=1,3,4 data_start=5`
- Key candidates: `ItemID` (matches the `CamelCase + ID` pattern)
- Sample rows showing real data starting at row 5

Note: the Item sheet has 4 header rows but the other sheets don't. In a real project you'd typically run inspect once per "header pattern group", or accept that LocText and Reward will show suboptimal sample data when forced to `field-row 2`. That's a known limitation — single inspect run per uniform-header set.

For LocText alone (different header):

```bash
python3 scripts/inspect_config_tables.py \
  --root examples/sample.xlsx \
  --field-row 2 \
  --meta-rows 1 \
  --format md
```

## 2. Patch — dry-run first

```bash
python3 scripts/patch_xlsx.py \
  --source examples/sample.xlsx \
  --output examples/sample_candidate.xlsx \
  --patch examples/sample-patch.json \
  --dry-run
```

Expected output (abbreviated):

```
# Patch Dry Run

## Sheet: Item
  field_row=2 meta_rows=[1, 3, 4] data_start_row=5

  Updates:
    row=5 col=2: Sword  =>  Long Sword
    row=7 col=5: 2  =>  3

  Appends:
    row=10: col1=10006, col2=Dagger, col3=Small fast weapon., ...

## Sheet: LocText
  field_row=2 meta_rows=[1] data_start_row=3

  Appends:
    row=8: col1=ITEM_10006_NAME, col2=匕首, col3=Dagger

Total: 2 update(s), 2 append row(s) across 2 sheet(s).
Dry run only — source workbook was not modified, no output file written.
```

If anything looks wrong (row index off, field name wrong, value mistyped), stop and fix the patch JSON now — before writing.

## 3. Patch — apply

```bash
python3 scripts/patch_xlsx.py \
  --source examples/sample.xlsx \
  --output examples/sample_candidate.xlsx \
  --patch examples/sample-patch.json
```

Output:

```json
{
  "output": "examples/sample_candidate.xlsx",
  "sheets": [
    {"changed_cells": 8, "appended_rows": 1, "sheet": "Item"},
    {"changed_cells": 3, "appended_rows": 1, "sheet": "LocText"}
  ]
}
```

`sample.xlsx` is unchanged. `sample_candidate.xlsx` has yellow-highlighted edited cells.

## 4. Diff

```bash
python3 scripts/diff_config_tables.py \
  --source examples/sample.xlsx \
  --candidate examples/sample_candidate.xlsx \
  --output examples/diff.md
```

Open `examples/diff.md`. Expect:

- Item: 8 changed cells (2 updates × 1 cell + 1 append × 6 cells)
- LocText: 3 changed cells (1 append × 3 cells)
- Reward: 0 changed cells
- No formula changes
- No added/removed sheets

If you see unexpected changes (e.g. cells you didn't intend to modify, or formulas drifting), do NOT writeback — go back and fix the patch.

## 5. Cleanup

```bash
rm examples/sample_candidate.xlsx examples/inventory.md examples/diff.md
```

(The generated `examples/sample.xlsx` is reusable; leave it for repeat runs.)

## What to take away

The same three commands work on real projects:

```bash
python3 scripts/inspect_config_tables.py --root /your/config --field-row N --meta-rows R,R,R --format md --output inventory.md
python3 scripts/patch_xlsx.py --source your.xlsx --output your_candidate.xlsx --patch your-patch.json --dry-run
python3 scripts/patch_xlsx.py --source your.xlsx --output your_candidate.xlsx --patch your-patch.json
python3 scripts/diff_config_tables.py --source your.xlsx --candidate your_candidate.xlsx --output diff.md
```

For the patch JSON spec, see `references/patch-format.md`.
For the validation checklist (including openpyxl re-save caveats), see `references/validation-checklist.md`.
