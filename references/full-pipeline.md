# 完整流程(中 / 高风险任务)

主 SKILL.md 给的是 11 步固定流程 + 简单 case 直通车。**改 10+ 行 / 新 ID / 跨表 / 表结构变更** 时打开本文件 —— 8 段更细的命令模板和决策点。

## Contents

- [1. 发现](#1-发现)
- [2. 公式闸门](#2-公式闸门)
- [3. 建项目档案(可选)](#3-建项目档案可选)
- [4. 跟用户确认](#4-跟用户确认)
- [5. (中 / 高风险)用 spec 自我组织](#5-中--高风险用-spec-自我组织)
- [6. 生成副本](#6-生成副本)
- [`note` 字段(备注列)](#note-字段备注列)
- [7. 校验](#7-校验)
- [8. 交付](#8-交付)

## 1. 发现

```bash
python3 scripts/inspect_config_tables.py --root /path/to/config --format md --output /path/to/config/inventory.md
# 多行表头:
python3 scripts/inspect_config_tables.py --root /path/to/config --field-row 2 --meta-rows 1,3
# 跳过样例 patch:
python3 scripts/inspect_config_tables.py --root /path/to/config --ignore '*-patch.json'
# 同时生成一份 patch JSON 骨架(下一步直接在骨架上填,不用凭印象写):
python3 scripts/inspect_config_tables.py --root /path/to/config --patch-template /path/to/config/patch.json
```

> 上面例子里 root 是目录;如果 root 是 **单个文件**(`/path/to/sample.xlsx`),把 `--output` / `--patch-template` 改写到 **该文件的父目录**(`/path/to/`),不要拼成 `/path/to/sample.xlsx/inventory.md` —— 那是非法路径。详见 [`unknown-project-onboarding.md`](unknown-project-onboarding.md) 第 2 步。

inspect 现在会自动建议:**如果第 1 行像中文显示名、第 2 行像英文字段名,会提示 `--field-row 2 --meta-rows 1`**。看到 hint 跟用户确认一下再走。

**`--patch-template` 强烈推荐**:它会为每张 Excel sheet 预填 `field_row` / `meta_rows` / `data_start_row` / `key_field` 和 `_fields_available` 字段名列表。你只需要在 `updates` / `appends` 数组里加内容就行,**不要凭印象写 patch JSON 的 schema**。

## 2. 公式闸门

如果 inventory 里出现 `FORMULA WARNING`,先停下。告诉用户公式位置示例,让用户选择:清公式 / 粘贴为值、导出无公式版本,或沿用公式。

`patch_xlsx.py` 也会在 dry-run 和实际 patch 前检查源工作簿;只要还有公式就直接拒绝继续。

如果用户明确说公式要沿用 / 保留,按主 SKILL.md 的 *公式闸门 → 带公式流程* 处理,不要把 `--allow-formulas` 当普通开关。

## 3. 建项目档案(可选)

复杂项目首次接入时,**AI 内部** 用 [`project-profile-template.md`](project-profile-template.md) 走一遍流程,留底自己用。**不要丢给用户填**。

反复做同一个项目,按 [`config-reference-playbook.md`](config-reference-playbook.md) 搭知识层。

## 4. 跟用户确认

用大白话:动哪个文件、加 / 改 / 删哪几行、可能影响哪些别的表、只生成副本还是会覆盖、风险高低。

## 5. (中 / 高风险)用 spec 自我组织

**AI 内部** 用 [`change-spec-template.md`](change-spec-template.md) 整理思路 —— 给用户看一段话总结,完整 spec 自己留底,不要落盘给用户。

## 6. 生成副本

**patch JSON 的精确格式见 [`patch-format.md`](patch-format.md)**(不要凭印象写 — 用 inspect 的 `--patch-template` 拿骨架,在骨架上填)。

```bash
python3 scripts/patch_xlsx.py --source table.xlsx --output table_candidate.xlsx --patch changes.json --dry-run
python3 scripts/patch_xlsx.py --source table.xlsx --output table_candidate.xlsx --patch changes.json
```

`--source` 和 `--output` **必须是不同的文件**,脚本不会原地编辑 — 一开始就会报错。

如果 `--output` 已存在,默认会自动加时间戳(`table_candidate_20260512_103045.xlsx`),不会报错。要强制覆盖加 `--force`,要严格报错加 `--strict`。

如果 `--output` 所在目录写不进去(沙盒限制),脚本会 **自动 fallback 写到 `~/Downloads/<同名>`**,并在 stderr + 输出 JSON 里告诉你实际路径。把这个路径告诉用户即可。

## `note` 字段(备注列)

每个 update **可以加 `note`**(一句话说明改动原因)。如果表里有列叫 `备注` / `Note` / `Comment` 之类,patch_xlsx 会把这段文本写到这一行的备注列里 —— 直接形成审计痕迹。

```json
{"key": "10003", "field": "Quality", "value": 3, "note": "品质 2 -> 3, 平衡性调整"}
```

**推荐**:每个改动都顺手填一句 `note`。表里看就知道这格谁改的、为什么。Appends 想填备注直接在 row 字典里写 `"备注": "..."`。

## 7. 校验

```bash
python3 scripts/diff_config_tables.py --source table.xlsx --candidate table_candidate.xlsx --output diff.md
# 沿用公式时,先用 Excel / WPS 或项目工具重算候选并保存,再加:
python3 scripts/diff_config_tables.py --source table.xlsx --candidate table_candidate.xlsx --output diff.md --compare-formula-results
# 跨表引用对账:
python3 scripts/validate_refs.py --workbook table_candidate.xlsx --field-row 2 --meta-rows 1,3,4
```

带公式流程里,`missing_formula_results` 非 0 = 候选还没有可读的公式计算结果,不能覆盖。`formula_result_changes` 不是自动失败,但必须逐项对照"最终要的结果"确认。

`validate_refs.py` 自动检测「`Item.LocKey` 指向 `LocText.LocKey`」这种引用,跑出来如果有 orphan,**先解决再覆盖**。

[`validation-checklist.md`](validation-checklist.md) 是 **AI 内部** 走清单用 —— 给用户一段话总结就行。

## 8. 交付

- 副本绝对路径
- 一段话:改了什么
- 需要用户决定的事
- 能不能帮他覆盖,还是他自己拷(参见 [`sandbox-writeback.md`](sandbox-writeback.md))
