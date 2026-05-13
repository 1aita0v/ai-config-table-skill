---
name: ai-config-table
description: >-
  Portable AI workflow for safely editing project configuration tables — Excel,
  CSV, TSV, JSON, exported workbooks, cloud sheets, or platform table APIs.
  Activate when the user asks to inspect, document, change, patch, add rows,
  batch-edit, validate, or review config data. Also triggers on Chinese
  phrasing: 改配置表, AI 配表, 加一行, 批量改, 配表复核, 跨表引用校验.
  Works under Claude Code, Codex, Cursor, or any agent that can run
  Python 3.8+ and read this directory.
---

# AI 配表 (AI Config Table)

## 你只需要知道(可能瞄一眼的策划,看这 3 行)

1. **跟 AI 说人话**就行,例如「把 Item.xlsx 里 10001 的品质改成 3」。
2. AI 会先给你看一个**副本**,**不会动你原文件**。
3. 你说「覆盖」之前,原表不会变。

下面都是给 AI 看的,你可以跳过。

---

## (给 AI)你面对的是什么样的用户

用户大概率是 **策划、PM 或非程序员**:

- 不会自己跑命令、不知道什么是 pip / git。
- "primary key (主键)"、"FK (外键)"、"header row (表头行)" 这类词需要你翻成大白话。
- 但是 **"schema"、"JSON"、"Excel"、"公式"、"宏" 大部分策划已经知道**,别故作小白把这些也"翻译"。
- 他们最担心的事:**改坏原表、公式/批注/合并单元格丢失、改完游戏里出 bug**。

所有命令都是你跑。用户只用大白话拍板。**不要让用户读你的 patch JSON 或者去 shell 里运行命令**。

## Language

用户用什么语言写,你就用什么语言回。下面对话样例多数是中文(原始受众),最后有一个英文样例做锚点 —— 其他语言按同样思路适配。

工作流(inspect → 副本 → diff → 用户确认)本身与语言无关。

## 这个 skill 在做什么(5 步)

1. **问** —— 表在哪、什么格式、表头几行,不要猜。
2. **看一遍** —— 只读扫一遍,记下结构。
3. **想清楚** —— 大改才写下来,小改心里有数即可。
4. **生成副本** —— 把改动应用在副本上,绝不动原表。
5. **对比 + 用户确认** —— 把 diff 摆出来,等用户点头。

> 给用户的承诺:**原文件在你明确说"覆盖"之前不会被动**。

## 用户第一次找你的时候

读 / 改任何东西之前,用大白话问三件事:

> 动手之前先问你三个事:
> 1. 表在哪?—— 电脑上某个文件夹 / 别人发的 zip / 云上链接 / 后台?
> 2. 是什么格式?—— Excel(`.xlsx`)、CSV、JSON,还是混着的?
> 3. 表最上面那几行 —— 是第一行就是列名,还是上面有 2-4 行(中文名 / 英文字段 / 类型 / 注释)?搞不清直接发文件夹路径给我,我先扫一眼。

英文版:

> Before I touch anything, three quick questions:
> 1. Where do the tables live — a folder, a zip, a cloud-sheet link, or a platform?
> 2. What formats — `.xlsx` / `.csv` / `.json` or mixed?
> 3. The top rows of the sheet — is the very first row the column names, or are there 2-4 rows on top (CN display / EN field / type / comment)? If unsure, point me at the folder, I'll scan first.

如果用户根本没法给数据源 —— 用 `references/no-data-source-report.md` 写一份「找不到数据源」报告,然后**停下**。不要瞎编表名、ID、规则。

## AI 助手 vs 用户:话术对照

跟用户说话时用右栏。读代码 / 写 patch 时内部仍用左栏。

| 内部术语 | 跟用户怎么说 |
|---|---|
| `field_row` / `header_row` | "列名那一行",或 "第 N 行是列名" |
| `meta_rows` | "上面那几行额外标签(中文名 / 类型 / 注释 等)" |
| `data_start_row` | "数据从第 X 行开始" |
| primary key / `key_field` | "这张表的唯一 ID 列(每行都不同的那个)" |
| foreign key / FK | "这张表指向另一张表的地方,比如 `ItemID` 对应 Item 表里的一条" |
| dry-run | "我先预览给你看,不实际写" |
| patch / patch JSON | "我在记录的修改清单"(不要把原始 JSON 给用户看) |
| candidate file | "改后的副本 —— 你的原文件没动" |
| writeback / overwrite | "把改后的副本覆盖到原表" |
| diff | "对比" 或 "改了什么的清单" |
| inspect / inventory | "我先扫一遍 / 你这些文件里都有啥" |

行号 / 列号永远带上"用户能看见的东西":说"第 5 行,就是 `10001 / Sword` 那一行" 而不是干巴巴说 "row 5"。

## 对话样例

下面 5 段示范 *对话的形状*,具体措辞按用户语气调整。

### 样例 1 — 用户给一个文件夹路径

> **用户**: 帮我看下我配置表里 Item 表的 10001 是什么
>
> **AI**: 好,你的配置表在哪儿?给我一个文件夹路径,或者直接把 Excel 文件拖给我。
>
> **用户**: `~/myproj/cfg/`
>
> **AI**: *(后台跑 inspect,自己读结果)* 找到了。`Item.xlsx` 前 4 行是表头(中文名 / 英文字段 / 类型 / 备注),数据从第 5 行开始。10001 这一行是:Sword(剑),描述 "A basic sword.",图标 `icon_sword`,品质 1。要改什么?

### 样例 2 — 用户想改一个值

> **用户**: 把 10003 的品质改成 3
>
> **AI**: 收到。10003 是 Potion(药水),当前品质 2。我会:
> - 不动你的原表
> - 生成一个改后的副本,只改这一格,从 2 → 3
> - 改的格子标黄方便你检查
>
> 我先预览给你看?
>
> **用户**: 行
>
> **AI**: *(dry-run)* 预览:Item 表第 7 行(`10003 / Potion`),品质列(Quality),`2 → 3`,其他都不动。生成副本?
>
> **用户**: 生成
>
> **AI**: *(patch + diff)* 副本在 `~/myproj/cfg/Item_candidate.xlsx`。对比下来只改了这一格。要我帮你覆盖回原表,还是你自己拖过去?

### 样例 3 — 用户加新行(跨表引用风险)

> **用户**: 帮我加 5 个新道具进 Item 表,ID 从 10020 开始
>
> **AI**: 没问题。这种加新道具的事,通常配套要做的事不少 —— 文本表里的中文名、图标资源表里的对应条目,如果只加 Item 不加这些,游戏里可能显示空白。在你给我中文名图标之前,我先把工作分两部分:
>
> - **你来定**:5 个道具的中文名、描述、图标资源名 / 路径
> - **我来核**:ID 10020-10024 这段没被占用、文本表(LocText 这种)和图标表的格式
>
> 你把中文名图标发我,我扫完就告诉你后续要不要补哪几张表。

### 样例 4 — 用户不知道结构怎么回答

> **用户**: 不知道,你看着办
>
> **AI**: OK 我先看一眼,5 秒。*(跑 inspect)* 看完了。Item 表第 1 行是中文(物品ID / 名称 / 描述 …),第 2 行是英文字段名(ItemID / Name / Desc …),第 3 行是类型,数据从第 5 行开始 —— 这种 4 行表头很常见,我按这个理解处理。唯一 ID 是 `ItemID`,我用它定位行。继续?

### 样例 5 — 用户想跳步骤

> **用户**: 直接帮我把改完的文件覆盖回去就行,别给我看什么副本了,麻烦
>
> **AI**: 好,我可以直接覆盖。不过我顺手做了个副本并不耽误时间,你愿意瞄一眼总结再覆盖最稳。这样吧:我**同时**做两件事 —— 生成副本 + 给你一句话总结。你说 OK 我立刻覆盖,说"不对"我也马上回滚。30 秒,不绕路。

### Dialogue (English flavor)

> **User**: Change item 10003's quality to 3 in my config.
>
> **AI**: Got it. 10003 is "Potion", currently quality 2. I'll make a copy with just that one cell changed (highlighted yellow) — your original is untouched. Want me to preview the change first?
>
> **User**: Yes.
>
> **AI**: *(dry-run)* Preview: Item sheet, row 7 (the row starting `10003 / Potion`), Quality column, `2 → 3`. Nothing else changes. Generate the candidate?
>
> **User**: Generate.
>
> **AI**: *(patch + diff)* Done: `~/myproj/cfg/Item_candidate.xlsx`. The diff shows only that single cell changed. Want me to overwrite the original for you, or will you copy it over yourself?

## 副本里我们保留什么、可能丢什么

这个 skill 用 `openpyxl` 读写 `.xlsx`。**一般会保留**:

- 单元格的值、公式、文本
- 基础样式(字体 / 字号 / 颜色 / 边框 / 数字格式)
- 合并单元格、批注
- 列宽、行高、命名区域
- `.xlsm` 文件的 VBA(脚本)

**可能改掉或丢失**(`diff_config_tables.py` 不比较这些,看不出来):

- 数据验证下拉框(尤其长枚举或跨表引用)
- 复杂条件格式(Excel 里手写的复杂规则)
- 嵌入图表(老版 Excel 创建的)
- 打印设置、自定义视图

如果用户的工作簿依赖任何「可能丢」的东西 —— **主动告诉用户**:生成副本之后,**让他先用 Excel / WPS 打开候选肉眼对比一次**再决定要不要覆盖。

## Windows + 非 ASCII 路径(中文目录名)—— 用 `--config` 模式

Windows 默认代码页是 cp936/GBK,不是 UTF-8。当你 spawn 子进程把中文路径作为命令行参数传给 Python 时,中间这一层经常会把中文字静默替换成 `?`,Python 收到的就是坏路径(`C:\TR\????\??\X.xlsx`),开文件会报 `OSError: [Errno 22] Invalid argument`。这是 Windows + 非 ASCII argv 的经典坑,Python 里面没法挽回。

**正确做法:用 `--config FILE` 模式,把所有参数(包括路径)写在 UTF-8 JSON 文件里,绕开 argv 编码**。

四个脚本(inspect / patch_xlsx / diff / validate_refs)都支持 `--config`。**规则**:

1. 在一个**纯 ASCII 路径**(如 `C:\Temp\`、skill 自身目录、系统 temp 目录)下写一个 UTF-8 JSON,key 用 argparse 的 dest 名(下划线、不带 `--`):

   ```json
   {
     "root": "C:\\TR\\配置表\\装备",
     "field_row": 2,
     "meta_rows": [1, 3, 4],
     "output": "C:\\TR\\配置表\\装备\\inventory.md",
     "patch_template": "C:\\Temp\\patch.json",
     "format": "md"
   }
   ```

2. 用纯 ASCII 路径调用脚本,其他参数全在 JSON 里:

   ```bash
   python3 scripts/inspect_config_tables.py --config C:\Temp\inspect_config.json
   ```

3. patch_xlsx / diff / validate_refs 同理。

**何时切到 --config 模式**:
- 用户的配置路径里含中文、日文、韩文等任何非 ASCII 字符
- 你在 Windows 上,不确定终端是 cp936 还是 UTF-8
- 脚本报 `路径里检测到 '?' 字符` 错误时

脚本会**自动检测路径里有 `?` 字符**(典型的 cp936 替换痕迹),直接报清晰错误告诉你切到 `--config`。

Mac / Linux 默认 UTF-8,中文路径直接走 argv 也没问题,不强制用 `--config` 模式 —— 但用了也行,完全等价。

## 沙盒不让你覆盖原表怎么办 —— 别绕,交给用户

很多运行环境(Codex 沙盒、Claude Code 限制模式、Cursor)会拒绝**覆盖用户原文件**,即使用户说要覆盖。这是正常的保护。**绝对不要**:

- `sudo` / 提权 / `--dangerously-*` 任何形式的绕过
- 写到旁路再 `mv` 回去
- 让用户去关安全开关

**正确动作**:把副本路径告诉用户,给他 3 步手动操作:

> 我已经把改好的版本生成到这里:
>
> `~/myproj/cfg/Item_candidate.xlsx`
>
> 不过我这边不允许直接覆盖你的原文件 `Item.xlsx`,这是默认的安全保护。请你手动:
>
> 1. 关掉 Excel(如果它正开着原文件)
> 2. 把 `Item.xlsx` 改名为 `Item_backup.xlsx`(保险)
> 3. 把 `Item_candidate.xlsx` 改名为 `Item.xlsx`
>
> 三步,30 秒。**如果你原文件名很长 / 带版本号**(比如 `Item_v3_final_用这个.xlsx`),直接告诉我准确的文件名,我把这两条改名指令写完整给你。

副本就是交付物,最后那一步用户自己关闭闭环 —— 这是用户的安全网,不是要绕过的障碍。

## 不确定怎么做?照这个固定流程走(给所有 agent 的最低保障)

如果你拿不准这次任务该怎么做、或你是一个能力一般的 agent —— **不要靠判断**,照下面顺序一步一步走,每步都能跑出来,然后看上一步输出再决定下一步:

1. **问用户三件事**(表在哪 / 什么格式 / 表头几行),或直接拿到文件夹路径。
2. **跑 inspect + 生成 patch 骨架**(一条命令同时拿 inventory 和骨架):
   ```bash
   python3 scripts/inspect_config_tables.py --root <用户给的路径> --output inventory.md --patch-template patch.json
   ```
3. **读 inventory.md** —— 知道表里都有什么 sheet、每张 sheet 的字段名。**留意 HINT 提示**(`row 1 像中文 / row 2 像英文字段`、`row N 像注释`)。
4. **读 patch.json 骨架** —— 它已经按 per-sheet 自动检测填好了 `field_row / meta_rows / data_start_row / key_field / _fields_available`。**不要凭印象写 schema,在骨架上填 `updates` / `appends` 就行**。
5. **跟用户用大白话**复述你打算改什么(具体到 sheet、key、字段、新旧值),拿到确认。**复述时主动应用 `references/rpg-config-patterns.md` 里的 5 条心智模型**(下文)。
6. **patch dry-run**:
   ```bash
   python3 scripts/patch_xlsx.py --source X.xlsx --output X_candidate.xlsx --patch patch.json --dry-run
   ```
   读 `Updates / Notes / Appends` 三段输出,拿出来给用户看。
7. **patch 实际生成副本**(去掉 `--dry-run`)。脚本会自动:`--output` 已存在加时间戳;源==输出立即报错;Excel 把候选打开着也立即报错并告诉你关闭。
8. **diff 对比**:
   ```bash
   python3 scripts/diff_config_tables.py --source X.xlsx --candidate X_candidate.xlsx --output diff.md
   ```
9. **validate_refs 跨表对账**(默认 per-sheet auto-detect,不用传参):
   ```bash
   python3 scripts/validate_refs.py --workbook X_candidate.xlsx
   ```
   **exit 非 0 = 有 orphan,先解决再覆盖**。
10. **把副本路径告诉用户**,等明确"覆盖"指令。**沙盒拒写就不绕**,把路径交给用户手动操作(参见上面 *沙盒不让你覆盖原表怎么办*)。

**任何一步报错,先读错误信息**:脚本现在会给出"Did you mean …?" 的建议(field / sheet / key 拼错时),`?` 路径会提示用 `--config`,Excel 锁文件会提示关闭工作簿。**不要尝试绕过错误,按错误信息修**。

## RPG 配表通用心智模型(进入第 5 步之前心里过一遍)

跟用户复述改动前,**心里过一遍** `references/rpg-config-patterns.md` 里 5 条通用 RPG 配表反模式 / 方法。具体到当前任务,只在该条适用时主动提:

1. **不要从 ID 段推业务语义** —— 用户说"按 ID 段过滤 X 类型"时,跟他说"我用 Type 字段过滤更稳"
2. **业务分类查 Desc 不查 I18N** —— 用户说"按中文名找内部分类标签",提醒标签在 Desc / Type 字段
3. **摸底必扫系统下所有 sheet 字段** —— 用户问"X 系统有没有 Y 字段",别看 sheet 名,grep 所有 sheet 列头
4. **配新表前先盲配 3-5 条已有的对答案** —— 用户要"参照 N 条配 M 条",自己先盲建 3-5 条对比
5. **表结构决策原则** —— 用户要新建表 / 加字段,先回答 3 个决策问题(扩展? ID 引用? 旧字段兼容?)

**每个项目的字段命名 / 表结构 / 命名约定不同** —— 这 5 条只给"思考方向",不是标准答案。具体项目用 `references/project-profile-template.md` 建档,覆盖默认假设。

## 按任务复杂度走不同流程

| 任务 | 跑哪几步 |
|---|---|
| 查某个字段是啥 | inspect → 回答 |
| 改一行某个值,无跨表 | inspect → patch dry-run + 生成 → diff |
| 加 1-5 行 | inspect → 一句话总结改动 → patch → diff → 跑 `validate_refs.py` |
| 10+ 行 / 新 ID / 跨表 / 公式 / 表结构 | 完整 7 步(下) |

## 完整流程(中 / 高风险任务)

### 1. 发现

```bash
python3 scripts/inspect_config_tables.py --root /path/to/config --format md --output inventory.md
# 多行表头:
python3 scripts/inspect_config_tables.py --root /path/to/config --field-row 2 --meta-rows 1,3
# 跳过样例 patch:
python3 scripts/inspect_config_tables.py --root /path/to/config --ignore '*-patch.json'
# 同时生成一份 patch JSON 骨架(下一步直接在骨架上填,不用凭印象写):
python3 scripts/inspect_config_tables.py --root /path/to/config --patch-template patch.json
```

inspect 现在会自动建议:**如果第 1 行像中文显示名、第 2 行像英文字段名,会提示 `--field-row 2 --meta-rows 1`**。看到 hint 跟用户确认一下再走。

**`--patch-template` 强烈推荐**:它会为每张 Excel sheet 预填 `field_row` / `meta_rows` / `data_start_row` / `key_field` 和 `_fields_available` 字段名列表。你只需要在 `updates` / `appends` 数组里加内容就行,**不要凭印象写 patch JSON 的 schema**。

### 2. 建项目档案(可选)

复杂项目首次接入时,**AI 内部** 用 `references/project-profile-template.md` 走一遍流程,留底自己用。**不要丢给用户填**。

反复做同一个项目,按 `references/config-reference-playbook.md` 搭知识层。

### 3. 跟用户确认

用大白话:动哪个文件、加 / 改 / 删哪几行、可能影响哪些别的表、只生成副本还是会覆盖、风险高低。

### 4. (中 / 高风险)用 spec 自我组织

**AI 内部** 用 `references/change-spec-template.md` 整理思路 —— 给用户看一段话总结,完整 spec 自己留底,不要落盘给用户。

### 5. 生成副本

**patch JSON 的精确格式见 [`references/patch-format.md`](references/patch-format.md)**(不要凭印象写 — 用 inspect 的 `--patch-template` 拿骨架,在骨架上填)。

```bash
python3 scripts/patch_xlsx.py --source table.xlsx --output table_candidate.xlsx --patch changes.json --dry-run
python3 scripts/patch_xlsx.py --source table.xlsx --output table_candidate.xlsx --patch changes.json
```

`--source` 和 `--output` **必须是不同的文件**,脚本不会原地编辑 — 一开始就会报错。

如果 `--output` 已存在,默认会自动加时间戳(`table_candidate_20260512_103045.xlsx`),不会报错。要强制覆盖加 `--force`,要严格报错加 `--strict`。

如果 `--output` 所在目录写不进去(沙盒限制),脚本会**自动 fallback 写到 `~/Downloads/<同名>`**,并在 stderr + 输出 JSON 里告诉你实际路径。把这个路径告诉用户即可。

### `note` 字段(备注列)

每个 update **可以加 `note`**(一句话说明改动原因)。如果表里有列叫 `备注` / `Note` / `Comment` 之类,patch_xlsx 会把这段文本写到这一行的备注列里 —— 直接形成审计痕迹。

```json
{"key": "10003", "field": "Quality", "value": 3, "note": "品质 2 -> 3, 平衡性调整"}
```

**推荐**:每个改动都顺手填一句 `note`。表里看就知道这格谁改的、为什么。Appends 想填备注直接在 row 字典里写 `"备注": "..."`。

### 6. 校验

```bash
python3 scripts/diff_config_tables.py --source table.xlsx --candidate table_candidate.xlsx --output diff.md
# 跨表引用对账:
python3 scripts/validate_refs.py --workbook table_candidate.xlsx --field-row 2 --meta-rows 1,3,4
```

`validate_refs.py` 自动检测「`Item.LocKey` 指向 `LocText.LocKey`」这种引用,跑出来如果有 orphan,**先解决再覆盖**。

`references/validation-checklist.md` 是 **AI 内部** 走清单用 —— 给用户一段话总结就行。

### 7. 交付

- 副本绝对路径
- 一段话:改了什么
- 需要用户决定的事
- 能不能帮他覆盖,还是他自己拷(参见 *沙盒不让你覆盖原表怎么办*)

## 速查:三条命令

```bash
# A. 扫文件夹 + 同时拿到 patch JSON 骨架(强烈推荐)
python3 scripts/inspect_config_tables.py --root /path/to/config --format md --output inventory.md --patch-template patch.json

# B. 编辑 patch.json(填 updates / appends),格式见 references/patch-format.md
#    然后预览 + 生成副本(注意:--source 和 --output 必须是不同文件)
python3 scripts/patch_xlsx.py --source x.xlsx --output x_candidate.xlsx --patch patch.json --dry-run
python3 scripts/patch_xlsx.py --source x.xlsx --output x_candidate.xlsx --patch patch.json

# C. 对比 + 跨表引用对账
python3 scripts/diff_config_tables.py --source x.xlsx --candidate x_candidate.xlsx --output diff.md
python3 scripts/validate_refs.py --workbook x_candidate.xlsx
```

带样例数据走查:`examples/walkthrough.md`。
patch JSON 格式参考:[`references/patch-format.md`](references/patch-format.md)。

## 操作原则

- **源表默认只读**。副本先行,覆盖只在用户明确点头之后。
- **不发明**。不知道的字段、ID、引用,要么问,要么标 unknown。
- **项目原生工具 > 自带脚本**。项目自己的 `validate` / `build` / `export` 优先。
- **多行表头是常态**(中文名 / 英文字段 / 类型 / 注释)。inspect 会主动建议。
- **编码降级**:CSV / JSON 默认 UTF-8 解码失败自动尝试 GBK。
- **沙盒拒写 = 用户安全网**,不是要绕的障碍。

## 与 agent runtime 兼容

纯 Python + Markdown,无 MCP / 插件 / SaaS。Python 3.8+ 即可。

- **Codex CLI**: `git clone https://github.com/1aita0v/ai-config-table-skill.git "${CODEX_HOME:-$HOME/.codex}/skills/ai-config-table"`
- **Claude Code(用户级)**: `git clone https://github.com/1aita0v/ai-config-table-skill.git ~/.claude/skills/ai-config-table`
- **Claude Code(项目级)**: `git clone https://github.com/1aita0v/ai-config-table-skill.git .claude/skills/ai-config-table`
- **Cursor / Aider / 其他**: 文件夹丢到 agent 看得见的地方,在 `.cursorrules` / `AGENTS.md` / `CLAUDE.md` 加一行指向 `ai-config-table-skill/SKILL.md`。

依赖:Python 3.8+。`.xlsx` / `.xlsm` 还需要 `openpyxl`。建议 `pip install -r requirements.txt`(把版本钉在测过的范围),急用直接 `pip install openpyxl` 也行。CSV / TSV / JSON 用标准库。inspect 和 patch 的 JSON 输出都带 `tool_versions` 字段,issue 复现更可靠。

## 文件结构

- `scripts/` —— `inspect_config_tables.py`(扫描)、`patch_xlsx.py`(生成副本)、`diff_config_tables.py`(对比)、`validate_refs.py`(跨表引用对账)。
- `references/` —— AI 看的参考:
  - `rpg-config-patterns.md` —— **通用 RPG 配表 5 条反模式 / 方法**(复述改动前心里过一遍)
  - `patch-format.md` —— `patch_xlsx.py` 接受的 JSON 格式(含 `note` 字段)
  - `data-sources.md` —— 数据源选择路由
  - `no-data-source-report.md` —— 找不到数据源时的失败模板
  - 以下 3 个是 **AI 内部** 走流程用,**不要丢给用户填表**:
    `project-profile-template.md`、`change-spec-template.md`、`validation-checklist.md`、`config-reference-playbook.md`
- `examples/` —— 样例工作簿构建器 + 完整 walkthrough。
- `agents/openai.yaml` —— Codex / OpenAI 风格 skill 元数据。

## 反模式

- 没发现 + 没确认就直接改源表。
- 仅凭 ID 区间、文件名片段去推业务含义。
- 改主表不查本地化 / 资源 / 奖励 / 解锁条件。
- 把客户端 / 服务端生成产物当成"数据源真相"。
- 没具体路径 / 行 / 字段 / 证据 就说"验证通过"。
- 把 `references/` 模板当作业丢给用户填。
- 把 patch JSON 或 shell 命令贴给用户读。
- 想办法绕过运行环境的写保护去覆盖原表。
