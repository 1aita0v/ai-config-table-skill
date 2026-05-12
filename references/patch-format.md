# Patch 格式

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
- `updates` —— 单元格更新列表,支持按坐标或按 key 定位。
- `appends` —— 追加新行,按字段名或列字母指定。

`field_row` 和 `meta_rows` 全部省略时,脚本会猜单行表头(等同 V2 行为)。

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
- 已有的输出文件不会被覆盖,除非加 `--force`。
- 被改的单元格默认标黄,加 `--no-mark` 跳过。
- `.xlsm` 会保留 VBA。
- patch 过程中报错时,半成品候选文件会被自动删掉 —— 防止你误信坏文件。
