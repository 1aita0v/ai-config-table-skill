---
name: ai-config-table
description: >-
  Portable AI workflow for editing any project's configuration tables safely.
  Use whenever a user asks to inspect, document, change, generate, patch,
  validate, or review config data — local Excel/CSV/TSV/JSON files, exported
  workbooks, cloud sheets, or platform table APIs. Triggers include "AI配表",
  "读配置表", "改配置表", "加一行/新增一条", "批量改", "配表复核",
  "配表知识库", "跨表引用校验", "use this project's config tables". Works under
  Claude Code, Codex, Cursor, or any agent that can run Python 3.8+ and read
  this directory.
version: 5
---

# AI 配表 (AI Config Table)

## 你面对的是什么样的用户(agent 先读这一段)

用户大概率是 **策划、PM 或非程序员**。默认假设:

- 他们不会自己跑 Python 命令。
- 他们不知道 "主键 (primary key)"、"外键 (FK)"、"表头行 (header row)"、"schema"、"dry-run"、"JSON" 具体指什么。
- 他们只想:某一行的某个值改了 / 加一行 / 改一个数 —— 并且 **不把游戏 / 产品搞坏**。

你(agent)负责跑所有命令。用户只需要用大白话拍板。**不要把命令粘出来让用户自己跑。不要假设他们会读 `.json` 文件。** 翻译成人话。

如果你正准备说 "header_row=2" 或者 "改一下 patch JSON",停一下,换说法 —— 看下面 *跟非程序员说话* 那一节。

## 这个 skill 在做什么(大白话)

改别人的配置表的一套安全流程,5 步:

1. **问** 用户表在哪、里面有什么 —— 不要猜。
2. **看一遍** 表(只读),记下结构。
3. **想清楚** 怎么改,写一小段说明 —— 只有大改才需要。
4. **生成副本** 并把改动应用上去(永远不动原表)。
5. **对比** 副本 vs 原表,让用户看一眼再决定要不要真覆盖。

> 给用户的承诺:**原文件在你明确说"覆盖"之前不会被动一根毫毛**。

## 用户第一次找你的时候

读 / 改任何东西之前,先问清楚三件事。用大白话问,不要塞术语:

> 动手之前,先问你三个事:
> 1. 表在哪?—— 是你电脑上的某个文件夹,还是别人发的 zip,还是云上的某个表格链接,还是某个后台?
> 2. 是什么格式?—— Excel(`.xlsx`)、CSV、JSON,还是混着的?
> 3. 表最上面那几行 —— 是第一行就是列名,还是上面有 2-4 行(比如一行中文名、一行英文字段、一行类型、一行注释)?搞不清也没事,你把文件夹路径甩给我,我先看一眼再跟你确认。

如果用户根本没法给你任何数据源 —— 用 `references/no-data-source-report.md` 写一份「找不到数据源」的报告,然后 **停下**。不要瞎编表名、ID、规则。

## 跟非程序员说话(agent 内部术语对照表)

跟用户说话时用右边的说法;读文档、写 patch 时内部仍用左边的术语。

| 内部术语 | 跟用户怎么说 |
|---|---|
| `field_row` / `header_row` | "列名那一行",或 "第 N 行是列名" |
| `meta_rows` | "上面那几行额外的标签(中文名 / 类型 / 注释 等)" |
| `data_start_row` | "数据是从第 X 行开始的" |
| primary key / `key_field` | "这张表的唯一 ID 列(每一行都不同的那个)" |
| foreign key / 跨表引用 / FK | "这张表指向另一张表的地方",比如 "这里的 ItemID 对应 Item 表里的一条" |
| schema | "表结构",或 "这张表有哪些列" |
| dry-run | "我先预览给你看,不实际写盘" |
| patch JSON | "我在帮你攒的修改清单" —— 不要把原始 JSON 给用户看,除非他要 |
| candidate file | "改后的副本 —— 你的原文件没动" |
| writeback | "把改后的文件覆盖到原表上" |
| diff | "对比",或 "改了什么的清单" |
| inspect / inventory | "我先扫一遍 / 你这些文件里都有啥" |

万一要说一个行号或列号("第 5 行"、"D 列"),一定带上用户能看见的内容做参照:"第 5 行,就是 `10001 / Sword` 那一行"。

## 对话样例(具体怎么说话)

下面 5 个样例展示 *对话的形状*。具体措辞按用户的语气调整。

### 样例 1 —— 用户给一个文件夹路径

> **用户**: 帮我看下我配置表里 Item 表的物品 10001 是什么
>
> **你**: 好,你的配置表在哪儿?给我一个文件夹路径,或者直接把 Excel 文件拖给我也行。
>
> **用户**: `~/myproj/cfg/`
>
> **你**: *(在后台跑 `inspect_config_tables.py`,自己读结果)* 找到了。`Item.xlsx` 这个表,前 4 行是表头(中文名 / 英文字段 / 类型 / 备注),第 5 行开始是数据。10001 这一行是:Sword(剑),描述 "A sword.",图标 `icon_sword`,品质 2。要改它的什么字段?

### 样例 2 —— 用户想改一个值

> **用户**: 把 10001 的品质改成 3
>
> **你**: 收到。我会:
> - 不动你的原表 `Item.xlsx`
> - 生成一个改后的副本 `Item_candidate.xlsx`,只改 10001 这一行的品质,从 2 → 3
> - 改动的格子会标黄方便你检查
>
> 这样可以吗?(我先预览给你看,确认无误再实际生成副本)
>
> **用户**: 行
>
> **你**: *(dry-run,把计划改动用大白话讲)* 预览:Item 表第 5 行,品质列(第 5 列),`2` → `3`。其他都不动。生成副本?
>
> **用户**: 生成
>
> **你**: *(跑 patch,再跑 diff)* 已生成 `~/myproj/cfg/Item_candidate.xlsx`。对比下来只动了这一格,其他完全一致。你打开看一下,如果 OK 我可以帮你把它覆盖回原表(`Item.xlsx`),或者你自己拖过去也行。

### 样例 3 —— 用户要加新行(有跨表风险)

> **用户**: 帮我加 5 个新道具进 Item 表,ID 从 10020 开始
>
> **你**: 加 5 个新道具是中等复杂度的事 —— 因为新道具通常还要在「文本表」(给玩家看的中文名)和「图标 / 资源表」里也有对应条目,不然游戏里可能显示成空白或者报错。我先核对几件事:
> 1. 你这 5 个道具的中文名、描述、图标分别是什么?
> 2. ID 10020-10024 这段还没被占用吧?(我先扫一遍确认)
> 3. 文本表(LocText 这种)和图标列表里要不要我一起加?
>
> 你先告诉我前两个,第 3 个我扫完就有答案了。

### 样例 4 —— 用户不知道结构怎么回答

> **用户**: 不知道,你看着办
>
> **你**: 好,我先自己看一遍,5 秒。*(跑 inspect)* 看完了。你的 Item 表第 2 行是英文字段名(ItemID / Name / Desc / Icon / Quality),第 1 行是中文(物品ID / 名称 / 描述 / 图标 / 品质),第 3 行是类型,数据从第 5 行开始。这种 4 行表头很常见,我按这个理解处理。
>
> 唯一编号字段是 `ItemID`(物品ID 那一列),我会用它来定位你要改的行。有问题随时打断我。

### 样例 5 —— 用户想跳步骤,不知道有风险

> **用户**: 直接帮我把改完的文件覆盖回去就行,别给我看什么副本了,麻烦
>
> **你**: 理解你想省事。但配置表这种东西改错了通常很难发现 —— 等到游戏里出 bug 才发现就晚了。我建议这样:
> - 我还是先生成副本(自动的,你不用做什么)
> - 我给你一句话总结改了什么,你看一眼,说"OK"
> - 我再覆盖回原表
>
> 整个过程多 30 秒,但能避免改错。可以吗?(如果你坚持直接覆盖,我也照办,但我会先备份原表到 `Item_backup_YYYYMMDD.xlsx`。)

## 沙盒不让你覆盖原表怎么办 —— 别绕,直接交付

很多 agent 运行环境(Codex 沙盒、Claude Code 限制模式、Cursor 等)会拒绝 **覆盖用户的原配置文件**,哪怕用户明确说"覆盖"。这是正常的,是运行环境在保护用户。**绝对不要** 尝试:

- 用 `sudo` 或者提权重跑。
- 写到旁边路径然后用 shell `mv` 盖回去。
- 用 `cat > source.xlsx` 这种重定向绕过文件写检查。
- 关掉安全标志,加 `--dangerously-*` 之类的选项,或者让用户去关。

而是 **把副本文件路径告诉用户,让他自己手动覆盖**:

> 我已经把改好的版本生成到这里:
>
> `~/myproj/cfg/Item_candidate.xlsx`
>
> 不过我这边的运行环境不允许我直接覆盖你的原文件 `Item.xlsx`,这是默认的安全保护,正常的。请你手动操作一下:
>
> 1. 关掉 Excel(如果它正开着 `Item.xlsx`)
> 2. 把 `Item.xlsx` 重命名为 `Item_backup.xlsx`(保险起见)
> 3. 把 `Item_candidate.xlsx` 改名为 `Item.xlsx`
>
> 三步,30 秒。完成后告诉我一声,我可以再扫一遍确认它和我们刚才看到的副本一致。

这是真实反复发生过的痛点。干净地把球踢回给用户才是对的姿势 —— 副本文件就是交付物,最后那一步用户自己关闭闭环。

## 按任务复杂度走不同流程

简单问题别上完整流程。

| 任务 | 跑哪几步 |
|---|---|
| 查某个字段是啥意思 | inspect → 回答(不需要 spec) |
| 改某一行的某个值,无跨表影响 | inspect → patch(预览 + 生成)→ 对比 |
| 加 1-5 行 | inspect → 小 spec → patch → 对比 → 简单跨表检查 |
| 10+ 行 / 新 ID / 跨表引用 / 公式 / 表结构变更 | 走下面的完整 7 步流程 |

## 完整流程(中 / 高风险任务)

### 1. 发现 (Discover)

先建表清单,再去理解业务含义。这些命令是你跑 —— 不要让用户跑。

```bash
python3 scripts/inspect_config_tables.py --root /path/to/config --output inventory.json --format json
# 项目有 2 行以上表头:
python3 scripts/inspect_config_tables.py --root /path/to/config --field-row 2 --meta-rows 1,3 --output inventory.md --format md
```

云 / 平台数据源:列出工作簿,每张相关 sheet 拉表头 + 3-5 行样例;如果平台支持就导只读副本。记下:数据源、时间戳、用了什么工具 / 查询。

### 2. 建项目档案 (Profile)

填 `references/project-profile-template.md`,覆盖:

- 数据源 + 接入方式。
- 工作簿 / sheet 命名规则、表头几行、数据从第几行开始。
- 唯一 ID 列 + 新 ID 怎么分配。
- 跨表引用模式(哪张表指向哪张表)。
- 枚举 / 字典表。
- 本地化、提示文案、资源、道具、奖励、解锁条件 等表。
- "源表" 和 "生成产物" 的边界。

同一个项目要反复做配表工作的话,按 `references/config-reference-playbook.md` 搭一个 `config-reference/` 知识层。

### 3. 跟用户确认任务和风险

用大白话复述给用户:

- 你会动哪个文件 / 哪张 sheet / 哪一段。
- 加哪几行 / 改哪几行 / 删哪几行。
- 哪些别的表可能会受影响。
- 是只生成副本,还是也帮他覆盖原表。
- 风险:低 / 中 / 高。

高风险 = 改表结构、加新字段、跨表引用、公式、新 ID 分配、改枚举、改生成产物、或 10+ 行数据。

### 4. 写 spec(中 / 高风险才需要)

中 / 高风险改动,改数据之前先填 `references/change-spec-template.md`。给用户看一段话总结就行,完整 spec 自己留底。

### 5. 生成副本

优先用项目自带工具(`validate.py`、导出脚本 等)。没有的话:

```bash
python3 scripts/patch_xlsx.py --source table.xlsx --output table_candidate.xlsx --patch changes.json
```

**永远不覆盖原表**。原表和副本放一起,或写到任务输出目录。

### 6. 校验

```bash
python3 scripts/diff_config_tables.py --source table.xlsx --candidate table_candidate.xlsx --output diff.md
```

再过一遍 `references/validation-checklist.md`。注意里面列的 openpyxl 重新保存注意事项(数据验证下拉框、复杂条件格式、嵌入图表 等可能无法完美往返)。

### 7. 交付

告诉用户:

- 副本文件在哪(绝对路径)。
- 一段话总结改了什么。
- 哪些事要用户拍板才能继续。
- 你能不能帮他覆盖原表,还是要他自己手动拷过去(参见上面 *沙盒不让你覆盖原表怎么办*)。

## 速查:你实际会跑的三条命令

```bash
# A. 扫一个配置表文件夹
python3 scripts/inspect_config_tables.py --root /path/to/config --format md --output inventory.md

# B. 预览改动,再生成副本
python3 scripts/patch_xlsx.py --source table.xlsx --output table_candidate.xlsx --patch changes.json --dry-run
python3 scripts/patch_xlsx.py --source table.xlsx --output table_candidate.xlsx --patch changes.json

# C. 对比原表 vs 副本
python3 scripts/diff_config_tables.py --source table.xlsx --candidate table_candidate.xlsx --output diff.md
```

带样例数据的完整走查:`examples/walkthrough.md`。

## 操作原则

- **源表默认只读**。永远先做副本,只有用户明确点头才覆盖。
- **不发明**。不知道的字段、ID、引用,要么问,要么标 unknown。
- **项目原生工具 > 自带脚本**。如果项目有自己的 `validate`、`build`、`publish`、`lint`、`export`,优先用它们。
- **多行表头是常态**。游戏 / 产品配置常有 2-4 行表头(中文名 / 英文字段 / 类型 / 注释)。`inspect` 和 `patch` 都支持 `--field-row` 和 `--meta-rows`。
- **编码降级**。CSV / JSON 默认 UTF-8,解码失败自动尝试 GBK,并记下用了哪个编码。
- **能有独立的第二遍校验就用上**。产出这张表的 agent,不应该是它正确性的唯一证据。
- **沙盒拒写不是要绕过去的障碍**,是用户的安全网 —— 看上面的交付段落。

## 与各种 agent 兼容

这个 skill 就是纯 Python + Markdown —— 没有 MCP,没有插件,没有 SaaS。任何能跑 Python 3.8+ 的环境都能用。

常见安装路径:

- **Codex CLI**: `git clone https://github.com/1aita0v/ai-config-table-skill.git "${CODEX_HOME:-$HOME/.codex}/skills/ai-config-table"`
- **Claude Code(用户级)**: `git clone https://github.com/1aita0v/ai-config-table-skill.git ~/.claude/skills/ai-config-table`
- **Claude Code(项目级)**: `git clone https://github.com/1aita0v/ai-config-table-skill.git .claude/skills/ai-config-table`
- **Cursor / Continue / Aider / 其他**: 把文件夹放到 agent 能看到的地方,然后在项目规则文件(`.cursorrules`、`AGENTS.md`、`CLAUDE.md`)里加一行指向 `ai-config-table-skill/SKILL.md`。

依赖:Python 3.8+;处理 `.xlsx` / `.xlsm` 还需要 `openpyxl`(`pip install openpyxl`)。CSV / TSV / JSON 用 Python 标准库就够。脚本检测不到 openpyxl 会给出安装提示。

## 参考文档

- `references/data-sources.md` —— 本地 / 导出 / 云 / 平台 / 项目工具 路由。
- `references/no-data-source-report.md` —— 找不到数据源时的失败模板。
- `references/project-profile-template.md` —— 项目档案模板。
- `references/config-reference-playbook.md` —— 搭建项目级配表知识库。
- `references/change-spec-template.md` —— 中 / 高风险改动的 spec 模板。
- `references/validation-checklist.md` —— 验收清单 + openpyxl 重存注意事项。
- `references/patch-format.md` —— `patch_xlsx.py` 接受的 JSON 格式(含多行表头字段)。

## 自带脚本

- `scripts/inspect_config_tables.py` —— 扫本地配置文件,产出清单;支持多行表头和编码降级。
- `scripts/patch_xlsx.py` —— 复制工作簿,应用结构化更新 / 追加;`--dry-run` 只预览不写。
- `scripts/diff_config_tables.py` —— 对比原表和副本(单文件或目录);截断时会显眼地警告。

## 样例

`examples/` 含一个完整走查:

- `build_sample.py` —— 生成一个带多行表头的 3-sheet 样例工作簿。
- `sample-patch.json` —— 改一行 + 加一行(在两张 sheet 上)。
- `walkthrough.md` —— 三条命令复现,带预期输出。

## 反模式

- 还没发现和定义 spec 就直接改源表。
- 仅凭 ID 区间、文件名片段、显示名 去推业务含义。
- 改主表不查本地化 / 资源 / 奖励 / 解锁条件 等引用表。
- 把客户端 / 服务端的生成产物当成 "数据源真相",不看项目规则。
- 没有具体路径、行 ID、字段名、证据 就说 "验证通过"。
- 表实际有 2-4 行表头,你按单行表头处理。
- 把原始 JSON 或命令粘给用户,让他自己看 / 跑。
- 想办法绕过运行环境的写保护去覆盖原表 —— 永远把副本文件交给用户处理。
