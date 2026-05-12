# Patch Format

`scripts/patch_xlsx.py` accepts a JSON file:

```json
{
  "sheets": [
    {
      "sheet": "Item",
      "field_row": 2,
      "meta_rows": [1, 3],
      "data_start_row": 5,
      "key_field": "ItemID",
      "updates": [
        {
          "key": "10001",
          "field": "Name",
          "value": "NewName"
        },
        {
          "row": 12,
          "col": "D",
          "value": "Direct coordinate update"
        }
      ],
      "appends": [
        {
          "ItemID": "10002",
          "Name": "New Item",
          "Desc": "Description"
        }
      ]
    }
  ]
}
```

## Sheet Fields

- `sheet` — required sheet name.
- `field_row` — 1-based row index that holds machine-readable field names. Use this for multi-row headers. (Alias: `header_row` is still accepted for backward compatibility with V2 patches.)
- `meta_rows` — optional list of 1-based row indices that hold supplementary header info (Chinese display name, type annotation, comment). The patch script will not write into these rows; recorded purely for inventory clarity.
- `data_start_row` — optional first data row. If omitted, defaults to the row after the last of `field_row` / `meta_rows`.
- `key_field` — field name used by `updates` with `key`.
- `updates` — list of direct or key-based cell updates.
- `appends` — list of rows to append by field name or column letter.

If you omit `field_row` and `meta_rows` entirely, the script falls back to guessing a single-row header (same behavior as V2).

## Multi-Row Header Example

A typical game config sheet:

| Row | Content |
|---:|---|
| 1 | 道具ID / 名称 / 描述 / 图标   (Chinese display) |
| 2 | ItemID / Name / Desc / Icon  (English field names — the parser uses these) |
| 3 | int / string / string / string  (type annotations) |
| 4 | 主键 / 文本 / 文本 / 资源引用  (comments) |
| 5 | 10001 / Sword / A sword. / icon_sword  (first data row) |

Corresponding patch:

```json
{
  "sheets": [
    {
      "sheet": "Item",
      "field_row": 2,
      "meta_rows": [1, 3, 4],
      "data_start_row": 5,
      "key_field": "ItemID",
      "updates": [
        {"key": "10001", "field": "Name", "value": "Long Sword"}
      ]
    }
  ]
}
```

## Update Modes

Direct coordinate:

```json
{"row": 12, "col": "D", "value": "x"}
```

Key + field:

```json
{"key": "10001", "field": "Name", "value": "x"}
```

Key-based updates require `key_field` and a matching row in the sheet.

## Dry Run

```bash
python3 scripts/patch_xlsx.py --source a.xlsx --output a_candidate.xlsx --patch p.json --dry-run
```

Prints the planned cell changes (`sheet / row / col / before → after`) and append rows without writing to disk. Always dry-run before applying.

## Safety

- The source workbook is copied to `--output` before edits.
- Existing output is not overwritten unless `--force` is passed.
- Edited cells are marked yellow by default; pass `--no-mark` to skip.
- `.xlsm` files are loaded with VBA preservation.
- If patching errors out partway, the partially-written candidate is removed automatically so you don't trust a broken file.
