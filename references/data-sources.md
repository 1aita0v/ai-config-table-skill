# 数据源选择

决定怎么读取项目配置表时,参考本文档。

## 选源优先级

按以下顺序选数据源:

1. 项目明确声明的"数据源真相"。
2. 本地源 Excel / CSV / TSV / JSON 文件。
3. 项目导出文件 —— 仅在文档确认它是权威的情况下。
4. 云表格或表格平台(有读 / 导出权限)。
5. 项目自带的表格工具或 API。
6. 用户提供的样本文件。

未经用户明确同意,不要写远端数据源,也必须先过完整流程的验证。

如果一个数据源都拿不到,用 `no-data-source-report.md` 写一份"找不到数据源"的报告。**干净的失败比自信地猜要好**。

## 本地文件

用 `scripts/inspect_config_tables.py` 扫一个配置目录或选定文件:

```bash
python3 scripts/inspect_config_tables.py --root path/to/config --format md --output inventory.md
python3 scripts/inspect_config_tables.py --root path/to/config --format json --output inventory.json
```

支持 `.xlsx`、`.xlsm`、`.csv`、`.tsv`、`.json`。

## 导出文件

导出文件适合做发现和 diff。**编辑前先确认导出是权威的,还是从别的源生成的**。

记下:
- 导出路径
- 导出时间
- 来源项目 / 表名
- 公式 / 样式是否保留
- 是否包含隐藏列 / sheet

## 云表格

共享表格、在线数据库、后台面板、自建表格平台:

- 用 read/list/query API 做发现。
- 大量 diff 时优先导出离线副本。
- spec 里记下 table ID、view ID、sheet ID、版本号。
- 把"可见的列名"和"内部字段 ID"当作两件事。

## 项目工具和 API

很多团队已经有自己的导出 / 校验 / 发布脚本,优先用它们。

找找:
- `export`、`dump`、`build`、`validate`、`lint`、`check`、`publish` 脚本
- schema 文件
- 客户端 / 服务端生成数据
- 表字典
- 配置目录附近的 README 或文档

## 一定要记下的证据

每次:
- 数据源类型 + 路径 / 工具名
- 项目 / 表 / 工作簿 / sheet 标识
- 用了什么查询 / 过滤
- 时间戳
- 行数或使用范围
- 样本行 ID
- 临时导出路径(如有)
