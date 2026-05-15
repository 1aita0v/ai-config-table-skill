# Patch 格式

## Contents

- [JSON 顶层结构(示例)](#patch-格式)
- [Sheet 各字段含义](#sheet-各字段含义)
- [自动 `note`(备注列)](#自动-note备注列)
- [多行表头样例](#多行表头样例)
- [更新模式](#更新模式)
- [Dry Run](#dry-run)
- [安全保护](#安全保护)

---

`scripts/patch_xlsx.py` 接受一个 JSON 文件:

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
          "value": "直接按坐标改"
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

## Sheet 各字段含义

- `sheet` —— 必填,sheet 名。
- `field_row` —— 1-based,标记"字段名行"。多行表头必填。(别名:`header_row` 仍兼容 V2 patch。)
- `meta_rows` —— 1-based 列表,标记额外表头行(中文显示名、类型注释、注释)。patch 脚本不会写入这些行,仅供清单记录。
- `data_start_row` —— 可选,数据起始行。不填则默认为 `field_row` / `meta_rows` 最后一行的下一行。
- `key_field` —— `updates` 中按 `key` 定位用的字段名。
- `updates` —— 单元格更新列表,支持按坐标或按 key 定位。每个 update 可选 `note` 字段(见下)。
- `appends` —— 追加新行,按字段名或列字母指定。

`field_row` 和 `meta_rows` 全部省略时,脚本会猜单行表头(等同 V2 行为)。

## 自动 `note`(备注列)

如果 sheet 的某一列叫 `备注` / `注释` / `Note` / `Notes` / `Comment` / `Comments` / `Remark` / `Remarks`(大小写不敏感),patch_xlsx **会把它识别为 row-level 注释列**。给 update 加一个 `note` 字段,patch 会把这段文本写到这一行的备注列里:

```json
{
  "key": "10003",
  "field": "Quality",
  "value": 3,
  "note": "品质 2 -> 3, 因为新版本平衡调整 (用户 X 2026-05-12)"
}
```

如果 sheet 没有备注列,`note` 字段被忽略。

**对 appends 想填备注?** 直接在追加的 row 字典里写 `"备注": "..."` 即可(就当普通字段填)。

**推荐(给 AI)**:每个 update 都带 `note`,即使一句话。这样每次改动在表里直接可见,成为审计痕迹。

## 多行表头样例

一个典型的游戏配置 sheet:

| 行号 | 内容 |
|---:|---|
| 1 | 道具ID / 名称 / 描述 / 图标   (中文显示名) |
| 2 | ItemID / Name / Desc / Icon  (英文字段名 —— parser 用这一行) |
| 3 | int / string / string / string  (类型注释) |
| 4 | 主键 / 文本 / 文本 / 资源引用  (注释) |
| 5 | 10001 / Sword / A sword. / icon_sword  (第一行数据) |

对应 patch:

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

## 更新模式

按坐标:

```json
{"row": 12, "col": "D", "value": "x"}
```

按 key + 字段:

```json
{"key": "10001", "field": "Name", "value": "x"}
```

按 key 的更新需要 `key_field` 字段,且 sheet 里要有匹配的行。

## Dry Run

```bash
python3 scripts/patch_xlsx.py --source a.xlsx --output a_candidate.xlsx --patch p.json --dry-run
```

打印计划改动(`sheet / row / col / before → after`)和追加行,但不写盘。**实际执行前永远先 dry-run**。

## 安全保护

- 编辑前会先把源工作簿复制到 `--output`。
- 源工作簿里只要有公式,默认直接拒绝 patch。先让用户决定处理方式:清公式 / 粘贴为值、导出无公式版本,或明确沿用公式。
- 用户明确要沿用公式时,可加 `--allow-formulas`;dry-run 和输出 JSON 会保留 `formula_warning`,必须复述给用户,并要求候选用 Excel / WPS 或项目工具重算后再发布。
- 沿用公式的候选重算后,用 `diff_config_tables.py --compare-formula-results` 查看缓存计算结果;`missing_formula_results` 必须为 0,结果必须和用户确认的最终预期一致。
- `--output` 和 `--source` 是同一路径时,脚本直接报错,提示候选名(脚本绝不在原表上原地编辑)。
- 已有的输出文件不会被覆盖:默认自动加时间戳(`xxx_20260512_103045.xlsx`);加 `--force` 才覆盖;加 `--strict` 直接报错。
- 被改的单元格默认标黄(包括 note 写入的备注格),加 `--no-mark` 跳过。
- `.xlsm` 会保留 VBA。
- patch 过程中报错时,半成品候选文件会被自动删掉 —— 防止你误信坏文件。
- 如果 `--output` 所在目录无写权限(沙盒限制),自动回退写到 `~/Downloads/<同名>`,在 stdout JSON 和 stderr 都打提示。
