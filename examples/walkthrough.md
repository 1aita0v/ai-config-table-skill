# Walkthrough —— 三条命令跑一遍

完整跑一遍 inspect → patch → diff 的循环,跑在自动生成的样例工作簿上。

样例模拟典型的游戏配表:主表带多行表头(中文 + 英文字段 + 类型 + 注释),加一个文案表 + 奖励表。

## 0. 准备(一次性)

在 skill 根目录:

```bash
pip install openpyxl
python3 examples/build_sample.py
```

这会生成 `examples/sample.xlsx`,3 张 sheet:

| Sheet | 表头行数 | 数据行数 | 列数 |
|---|---|---|---|
| Item | 4(中文 / 英文 / 类型 / 注释) | 5 | 7(含「备注」列) |
| LocText | 2(中文 / 英文字段) | 5 | 3 |
| Reward | 1 | 3 | 3 |

`Item.备注` 是 row-level 注释列 —— patch_xlsx 会自动识别名为 `备注` / `Note` / `Comment` 等的列。给 update 加 `note` 字段,改动原因就会自动写到这一行的备注列里。

## 1. Inspect(同时生成 patch JSON 骨架)

用与 Item sheet 匹配的 field-row 跑 inspect,**顺手生成 patch 骨架**:

```bash
python3 scripts/inspect_config_tables.py \
  --root examples/sample.xlsx \
  --field-row 2 \
  --meta-rows 1,3,4 \
  --format md \
  --output examples/inventory.md \
  --patch-template examples/patch_template.json
```

打开 `examples/patch_template.json`,会看到为 Item / LocText / Reward 三张 sheet 都预填好了 `field_row` / `meta_rows` / `data_start_row` / `key_field`,你只需在 `updates` / `appends` 里写改动内容。**`_fields_available` 列出了可用的字段名 —— 不用再翻 inventory.md 抄字段**。

打开 `examples/inventory.md`,应该看到:

- Item sheet 标记 `field_row=2 meta_rows=1,3,4 data_start=5`
- 候选主键:`ItemID`(符合 `驼峰 + ID` 模式)
- 样本行从第 5 行开始

注意:Item sheet 有 4 行表头,另两张没有。实际项目里通常按"表头模式分组"分别跑 inspect,或接受 LocText 和 Reward 在 `field-row 2` 下显示次优样本。这是已知限制 —— 同一次 inspect 适用于同样表头模式的表集合。

对 LocText 单跑(表头不同):

```bash
python3 scripts/inspect_config_tables.py \
  --root examples/sample.xlsx \
  --field-row 2 \
  --meta-rows 1 \
  --format md
```

## 2. Patch —— 先 dry-run

```bash
python3 scripts/patch_xlsx.py \
  --source examples/sample.xlsx \
  --output examples/sample_candidate.xlsx \
  --patch examples/sample-patch.json \
  --dry-run
```

预期输出(简化):

```
# Patch Dry Run

## Sheet: Item
  field_row=2 meta_rows=[1, 3, 4] data_start_row=5 note_column=备注

  Updates:
    row=5 col=2(Name): Sword  =>  Long Sword
    row=7 col=5(Quality): 2  =>  3

  Notes:
    row=5 col=7(备注): (empty)  =>  改名 Sword -> Long Sword (用户请求)
    row=7 col=7(备注): (empty)  =>  品质 2 -> 3

  Appends:
    row=10: ItemID=10006, Name=Dagger, Desc=Small fast weapon., ...

## Sheet: LocText
  ...
  Appends:
    row=8: LocKey=ITEM_10006_NAME, TextCN=匕首, TextEN=Dagger

Total: 2 update(s), 2 note write(s), 2 append row(s) across 2 sheet(s).
Dry run only — source workbook was not modified, no output file written.
```

注意两条 update 都带了 `note`,所以多出来一段 **Notes:** 把改动原因写到备注列。如果你不想写备注,patch JSON 里不加 `note` 字段就行(整个 Notes 段消失)。

如果有任何不对的地方(行号错、字段名错、值打错),**立刻** 改 patch JSON,不要继续生成。

## 3. Patch —— 实际生成

```bash
python3 scripts/patch_xlsx.py \
  --source examples/sample.xlsx \
  --output examples/sample_candidate.xlsx \
  --patch examples/sample-patch.json
```

输出:

```json
{
  "output": "examples/sample_candidate.xlsx",
  "sheets": [
    {"changed_cells": 8, "appended_rows": 1, "sheet": "Item"},
    {"changed_cells": 3, "appended_rows": 1, "sheet": "LocText"}
  ]
}
```

`sample.xlsx` 没动。`sample_candidate.xlsx` 里被改的格子标了黄。

## 4. Diff

```bash
python3 scripts/diff_config_tables.py \
  --source examples/sample.xlsx \
  --candidate examples/sample_candidate.xlsx \
  --output examples/diff.md
```

打开 `examples/diff.md`,预期:

- Item:多个改动格 = 2 次 update × 1 格 + 2 次 note 写入 + 1 次 append(7 列)
- LocText:3 个改动格(1 次 append × 3 格)
- Reward:0 改动
- 没有公式改动
- 没有 sheet 增减

如果看到意料之外的改动(没打算动的格子动了,公式漂了),**不要** 覆盖回去 —— 回去改 patch。

## 5. 清理

```bash
rm examples/sample_candidate.xlsx examples/inventory.md examples/diff.md
```

(生成的 `examples/sample.xlsx` 可以保留,下次还能用。)

## 5b. 跨表引用对账(可选,但建议)

```bash
python3 scripts/validate_refs.py \
  --workbook examples/sample_candidate.xlsx \
  --field-row 2 \
  --meta-rows 1
```

会自动检测 `Item.LocKey → LocText.LocKey` 这种引用,跑出来如果有 orphan(候选里加了 Item 没加 LocText),会列出哪一行的哪个 LocKey 找不到对应。**这就是 agent 视角下"最值钱的兜底"**。

## 实际项目里也是同样的三条命令

```bash
python3 scripts/inspect_config_tables.py --root /your/config --field-row N --meta-rows R,R,R --format md --output inventory.md
python3 scripts/patch_xlsx.py --source your.xlsx --output your_candidate.xlsx --patch your-patch.json --dry-run
python3 scripts/patch_xlsx.py --source your.xlsx --output your_candidate.xlsx --patch your-patch.json
python3 scripts/diff_config_tables.py --source your.xlsx --candidate your_candidate.xlsx --output diff.md
python3 scripts/validate_refs.py --workbook your_candidate.xlsx --field-row N --meta-rows R,R,R
```

patch JSON 格式见 `references/patch-format.md`。
校验清单见 `references/validation-checklist.md`。
