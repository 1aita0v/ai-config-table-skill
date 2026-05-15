---
name: ai-config-table
description: >-
  Safely edit project configuration tables — Excel (.xlsx/.xlsm), CSV, TSV,
  JSON, game design spreadsheets, item tables, drop tables, skill tables,
  buff tables, equipment tables, quest tables, localization (LocKey) tables,
  numeric balance sheets, level configs, reward tables, exported workbooks.
  Pipeline: scan → formula gate → preview → candidate copy → diff → cross-sheet
  foreign-key check → user confirms overwrite. Also triggers on Chinese:
  改配置表, AI 配表, 加一行, 批量改, 配表复核, 跨表引用校验, 盘点配置,
  策划表, 数值表, 道具表, 技能表, 装备表, 任务表, 掉落表, 本地化表.
allowed-tools: Bash, Read, Edit, Write, Grep, Glob
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

用户用什么语言写,你就用什么语言回。下面对话样例多数是中文(原始受众),英文样例做锚点 —— 其他语言按同样思路适配。工作流(inspect → 副本 → diff → 用户确认)本身与语言无关。

## 这个 skill 在做什么(6 步)

1. **问** —— 表在哪、什么格式、表头几行,**不要猜、不要凭 cwd 自作主张开扫**。详见下方 *[装完之后第一句话](#装完之后第一句话--永远先问路径不许凭-cwd-开扫)*。
2. **看一遍** —— 只读扫一遍,记下结构;inspect 自动扫出 **"配表规律候选"**(ID 段、隐藏列、LocKey 模板、目录布局 等 8 类),AI 跟用户确认后入档。
3. **公式闸门** —— 源表只要有公式,先停下确认处理方式:转值 / 导出无公式 / 明确沿用公式。
4. **想清楚** —— 大改才写下来,小改心里有数即可。
5. **生成副本** —— 把改动应用在副本上,绝不动原表。
6. **对比 + 用户确认** —— 把 diff 摆出来,等用户点头。

> 给用户的承诺:**原文件在你明确说"覆盖"之前不会被动**。

## 简单 case 直通车

**90% 的任务** —— 单仓 / 单人 / 改 1 格 / 没多版本 —— 你只需要看 3 节:

1. *[公式闸门](#公式闸门先确认处理方式)* —— 源表有公式先停,选转值 / 沿用
2. *[不确定怎么做?照这个固定流程走](#不确定怎么做照这个固定流程走给所有-agent-的最低保障)* —— inspect → patch dry-run → patch → diff → validate_refs
3. *[反模式](#反模式)* —— 看一眼别踩

**下面这些章节只在以下信号出现时打开**(全部在 references/,按需读):

| 触发信号 | 打开这节 |
|---|---|
| 装完 skill / 第一次接入不认识的库 / 不熟悉的库 | 主文档 *[装完之后第一句话](#装完之后第一句话--永远先问路径不许凭-cwd-开扫)* + [`references/unknown-project-onboarding.md`](references/unknown-project-onboarding.md) |
| `.ai-config-table/` 已存在(你不是第一个 AI) | [`references/successor-rules.md`](references/successor-rules.md) |
| 项目根有 `trunk/` + `version_*/`、分支独立仓、或跨仓拓扑(配置 SVN + 工程 git) | [`references/multi-version-cross-repo.md`](references/multi-version-cross-repo.md) |
| 用户描述模糊("世界 boss 那张表" / "ConditionExtra 啥意思") | [`references/ambiguous-input.md`](references/ambiguous-input.md) |
| 改 10+ 行 / 新 ID / 跨表 / 表结构变更 → 完整流程 | [`references/full-pipeline.md`](references/full-pipeline.md) |
| 需要入档项目记忆(`learn.py` 怎么用、什么时候入) | [`references/learn-howto.md`](references/learn-howto.md) |
| 副本里 openpyxl 可能丢的边角(线程批注 / 数据验证 / 富文本 等) | [`references/xlsx-roundtrip.md`](references/xlsx-roundtrip.md) |
| Windows + 中文路径报错 | [`references/windows-nonascii-paths.md`](references/windows-nonascii-paths.md) |
| 沙盒拒绝覆盖原表 | [`references/sandbox-writeback.md`](references/sandbox-writeback.md) |
| 想看更多对话样例(加新行 / 跨表 / 跳步骤 / 字段歧义) | [`references/dialogue-samples.md`](references/dialogue-samples.md) |

简单 case 直走 6 步,**不要先去读"后入者 / 多人 / 多版本"那一长段**,会浪费时间。

## 装完之后第一句话 —— 永远先问路径,不许凭 cwd 开扫

**装完 skill 后第一轮对话(或第一次接入不认识的库),不管用户说啥 —— 模糊的「帮我看看」「整理一下」、还是具体的「改 10001 品质」 —— 你的第一句回应永远是:**

> 好的。我先**只读扫一遍**,不动你任何原文件,扫完讲一段印象。你的配置表在哪儿?
> *(如果 cwd 看着像配置目录)* 看到 cwd 是 `<path>`,是这个吗?还是在别处?

**禁止动作清单**(命中任何一条就是反例):
- 看到 cwd 名字像 `xxx配置表` / `xxx_config` / `资源` / `data` 就直接 `ls` 开扫
- 内部独白里出现「**或者**我可以查看当前工作目录」「**既然 cwd 看着像配置目录**就...」 —— 这是给自己开口子的起手式,**列出了正确动作然后自己绕过去**,立刻停
- 没拿到用户对路径的确认就跑 `inspect_config_tables.py` 或任何 `find` / `grep`

Claude Code / Codex 的 cwd 经常**恰好**在用户项目里,但「恰好在」 ≠ 「用户授权扫」。**先问一句拿到点头再动**,这一秒钟的等待是用户对"不动我原文件"承诺的第一次兑现。

拿到路径确认后,按分流走:`<root-dir>/.ai-config-table/` 不存在或为空 → AI 不认识库 → [`references/unknown-project-onboarding.md`](references/unknown-project-onboarding.md);已存在且 `## Project Memory` 段有内容 → AI 已经认识 → 先读 [`references/successor-rules.md`](references/successor-rules.md) 再进任务。

## 数据源三件事问法(库 AI 已经认识时用)

读 / 改之前先确认数据源:

> 动手之前先问你三个事:
> 1. 表在哪?—— 电脑上某个文件夹 / 别人发的 zip / 云上链接 / 后台?
> 2. 是什么格式?—— Excel(`.xlsx`)、CSV、JSON,还是混着的?
> 3. 表最上面那几行 —— 是第一行就是列名,还是上面有 2-4 行(中文名 / 英文字段 / 类型 / 注释)?搞不清直接发文件夹路径给我,我先扫一眼。

英文版:

> Before I touch anything, three quick questions:
> 1. Where do the tables live — a folder, a zip, a cloud-sheet link, or a platform?
> 2. What formats — `.xlsx` / `.csv` / `.json` or mixed?
> 3. The top rows of the sheet — is the very first row the column names, or are there 2-4 rows on top (CN display / EN field / type / comment)? If unsure, point me at the folder, I'll scan first.

如果用户根本没法给数据源 —— 用 [`references/no-data-source-report.md`](references/no-data-source-report.md) 写一份「找不到数据源」报告,然后**停下**。不要瞎编表名、ID、规则。

## 公式闸门:先确认处理方式

有些人会在配置表里临时加公式。**这不是小风险**:一旦追加行、扩展数组列、调整行数配置,公式范围 / 缓存结果可能不会按预期重算,而 `diff` 只能看到公式文本或单元格值变化,看不出"算错了但公式还在"。

规则:

- Excel / WPS 工作簿里只要检测到公式,默认**不继续 patch**。哪怕公式不在这次目标列,也先停下问用户怎么处理。
- 告诉用户公式位置示例,让用户选:复制粘贴为值 / 导出无公式版本 / 明确保留并沿用公式。**不要替用户自动清公式**,因为 AI 不知道应该保留计算后的值、留空,还是保留某个中间态。
- 用户选择清公式后,重新跑 `inspect_config_tables.py`,确认没有 `FORMULA WARNING`,再继续 dry-run / patch。
- 用户明确说要保留 / 沿用公式,并接受公式重算风险时,才可以用 `--allow-formulas`。不要为了省事绕过公式闸门。

给用户的话术:

> 我扫到这个 Excel 里还有公式,先停一下。你想怎么处理:把公式复制粘贴为值、导出一份无公式版本,还是这些公式本来就要沿用?如果要沿用,我可以保留公式继续做候选,但候选生成后需要用 Excel/WPS 或项目导出工具重算一遍。

### 如果用户明确要沿用公式

这属于**带公式流程**,不是普通配表修改:

1. 先确认一句:"这些公式是这张表长期维护的一部分,不是临时计算用的吗?"
2. 告诉用户限制:脚本能保留 / 写入公式文本,但**不会像 Excel 一样重算结果**;如果下游读取的是 Excel 缓存值,必须由 Excel / WPS 或项目原生导出工具重算后再发布。
3. 先写清楚"最终要的结果":哪些公式格 / 派生字段应该算出什么值,或至少应该和哪些源字段 / 样本行一致。没有预期结果,就不能说验证通过。
4. 如果本次涉及新增行 / 扩展行数配置,必须明确新行的公式怎么来:复制上一行公式、按某个范围改引用、还是用户会自己补。没确认前不要猜。
5. 用户明确接受后,才可以在 dry-run 和 patch 命令加 `--allow-formulas`。dry-run / 输出 JSON 里的 `formula_warning` 必须复述给用户。
6. 生成候选后,用户需要用 Excel / WPS 打开候选让公式重算,或跑项目自己的导出 / 重算脚本。
7. 重算并保存后,用 `diff_config_tables.py --compare-formula-results` 检查缓存计算结果。`missing_formula_results` 非 0 说明没重算成功;`formula_result_changes` 要逐项对照第 3 步的预期结果。
8. 只有公式文本、公式算出的值、用户要的最终结果三者都对上,才继续 validate / 覆盖。

给用户的话术:

> 可以沿用公式,但这次就不是普通改表了。我可以用带公式模式保留这些公式,不过脚本不会帮 Excel 重算。你确认这些公式是要长期保留的,候选生成后会用 Excel/WPS 或项目导出工具重算一遍,并且告诉我关键公式格最终应该算成什么结果吗?

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

## 标准对话样例(改一格 = 最常用形态)

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

**更多形态**(用户给文件夹路径 / 加新行跨表 / 不知道结构怎么回答 / 想跳步骤 / 模糊 sheet 名 / 字段不懂含义 / 英文样例)→ [`references/dialogue-samples.md`](references/dialogue-samples.md)。

## 不确定怎么做?照这个固定流程走(给所有 agent 的最低保障)

如果你拿不准这次任务该怎么做、或你是一个能力一般的 agent —— **不要靠判断**,照下面顺序一步一步走,每步都能跑出来,然后看上一步输出再决定下一步:

1. **问用户三件事**(表在哪 / 什么格式 / 表头几行),或直接拿到文件夹路径。
2. **跑 inspect + 生成 patch 骨架**(一条命令同时拿 inventory 和骨架):
   ```bash
   python3 scripts/inspect_config_tables.py --root <用户给的路径> --format md --output <用户给的路径>/inventory.md --patch-template <用户给的路径>/patch.json
   ```
3. **读 inventory.md** —— 知道表里都有什么 sheet、每张 sheet 的字段名。**留意 HINT 提示**(`row 1 像中文 / row 2 像英文字段`、`row N 像注释`)。如果开头有 **`## Project Memory`** 段,**先读它**,把已知规律应用到本任务,不要重复问用户已经记录过的事。再扫一眼 **`## 配表规律候选`** 段(脚本扫出的 8 类规律,标"猜"),复述时主动应用,任务尾部跟用户确认是否入档。
4. **公式闸门** —— 如果 inventory 里有 `FORMULA WARNING`,或 `patch_xlsx.py` 报 "contains formula cell(s)",本轮先停,让用户决定处理方式:转值 / 导出无公式版本 / 沿用公式。用户明确要沿用公式时,走上面的"带公式流程"。
5. **读 patch.json 骨架** —— 它已经按 per-sheet 自动检测填好了 `field_row / meta_rows / data_start_row / key_field / _fields_available`。**不要凭印象写 schema,在骨架上填 `updates` / `appends` 就行**。
6. **按任务大小做差集**,拿到确认。**差集详细程度跟任务复杂度匹配,见下面 "差集详细程度按任务大小分级"**。复述时主动应用 [`references/rpg-config-patterns.md`](references/rpg-config-patterns.md) 里的 5 条心智模型。
7. **patch dry-run**:
   ```bash
   python3 scripts/patch_xlsx.py --source X.xlsx --output X_candidate.xlsx --patch patch.json --dry-run
   ```
   读 `Updates / Notes / Appends` 三段输出,拿出来给用户看。
8. **patch 实际生成副本**(去掉 `--dry-run`)。脚本会自动:`--output` 已存在加时间戳;源==输出立即报错;Excel 把候选打开着也立即报错并告诉你关闭。
9. **diff 对比**:
   ```bash
   python3 scripts/diff_config_tables.py --source X.xlsx --candidate X_candidate.xlsx --output diff.md
   ```
   带公式流程的额外步骤见 [`references/full-pipeline.md`](references/full-pipeline.md) 第 7 段。
10. **validate_refs 跨表对账**(默认 per-sheet auto-detect,不用传参):
   ```bash
   python3 scripts/validate_refs.py --workbook X_candidate.xlsx
   ```
   **exit 非 0 = 有 orphan,先解决再覆盖**。
11. **把副本路径告诉用户**,等明确"覆盖"指令。**沙盒拒写就不绕**,把路径交给用户手动操作(详见 [`references/sandbox-writeback.md`](references/sandbox-writeback.md))。
12. **任务结束前**,如果过程中发现了稳定的项目规律(命名约定 / 跨表对应 / 否决过的做法 等),**主动问用户**"要存到 `.ai-config-table/` 吗?",用户说存就跑 `scripts/learn.py`(详见 [`references/learn-howto.md`](references/learn-howto.md))。下次开工就少问一遍。

**任何一步报错,先读错误信息**:脚本现在会给出"Did you mean …?" 的建议(field / sheet / key 拼错时),`?` 路径会提示用 `--config`,Excel 锁文件会提示关闭工作簿。**不要尝试绕过错误,按错误信息修**。

> 中 / 高风险任务(改 10+ 行 / 表结构变更)走更细的命令模板和决策点 → [`references/full-pipeline.md`](references/full-pipeline.md)。

## RPG 配表通用心智模型(复述改动前心里过一遍)

跟用户复述改动前,**心里过一遍** [`references/rpg-config-patterns.md`](references/rpg-config-patterns.md) 里 5 条通用 RPG 配表反模式 / 方法。具体到当前任务,只在该条适用时主动提:

1. **不要从 ID 段推业务语义** —— 用户说"按 ID 段过滤 X 类型"时,跟他说"我用 Type 字段过滤更稳"
2. **业务分类查 Desc 不查 I18N** —— 用户说"按中文名找内部分类标签",提醒标签在 Desc / Type 字段
3. **摸底必扫系统下所有 sheet 字段** —— 用户问"X 系统有没有 Y 字段",别看 sheet 名,grep 所有 sheet 列头
4. **配新表前先盲配 3-5 条已有的对答案** —— 用户要"参照 N 条配 M 条",自己先盲建 3-5 条对比
5. **表结构决策原则** —— 用户要新建表 / 加字段,先回答 3 个决策问题(扩展? ID 引用? 旧字段兼容?)

**每个项目的字段命名 / 表结构 / 命名约定不同** —— 这 5 条只给"思考方向",不是标准答案。具体项目用 [`references/project-profile-template.md`](references/project-profile-template.md) 建档,覆盖默认假设。

## 按任务复杂度走不同流程

简单任务别上完整流程,**差集详细程度也跟着任务大小走** —— 不要 1 格改也搞 4 段汇报。

| 任务 | 跑哪几步 | 差集格式 |
|---|---|---|
| 查某个字段是啥 | inspect → 回答 | 不用差集 |
| 改一行某个值,无跨表 | inspect → 1 句话总结 → dry-run → 用户 OK → 生成 → diff | **1 句话**:"改 X 行 Y 字段 Z→W,其他不动" |
| 加 1-5 行 | inspect → **4 段差集** → dry-run → 生成 → diff → validate_refs | **4 段差集**(见下) |
| 源表有公式 | inspect / patch 报公式 → 先问用户处理方式;转值 / 无公式导出后重新 inspect,沿用公式则走带公式流程 | 先不生成差集,解除阻塞后再按原任务分级 |
| 10+ 行 / 新 ID / 跨表 / 表结构 | [`references/full-pipeline.md`](references/full-pipeline.md) + spec | **4 段差集 + spec 兜底** |

### 差集详细程度按任务大小分级

**简单任务(改 1 格)** —— 1 句话:

> 我打算改 Item 表第 7 行(`10003 Potion`)的品质,2 → 3,其他不动。预览一下?

**中等任务(加 1-5 行 / 涉及 2 张表)→ 4 段差集**:

| 段 | 内容 |
|---|---|
| **要改的** | 具体 sheet / key / field / 新旧值 |
| **不动的** | 显式列出"我刻意没动的相邻字段 / 相邻表",兜底用户即时纠正 |
| **请确认的** | 用户没明示但任务里隐含决策的事(附属表是否同步?备注写什么?口径有歧义?) |
| **我假设的** | AI 用经验补的默认值,写出来供用户纠错 |

样例:

> 动手前我列下计划:
>
> **要改**: Item 表加 3 个新道具(ID 10020-10022),Name / Desc / Icon / Quality 按你给的填,LocKey 按 `ITEM_<id>_NAME` 生成。LocText 表对应加 3 条 (LocKey / TextCN / TextEN)。
>
> **不动**: Item 表其他行;Reward / Drop 表的现有关联;图标资源表(没说要新增图标资源)。
>
> **请你确认**:
> - 图标用现有还是要让我列出来你挑?
> - 备注列写什么?(每行一句改动来源)
>
> **我假设的**:
> - 品质都是 1(没特别说就默认起始品质)
> - LocText 表 TextEN 我用音译,后续翻译同学再改
>
> 这样对吗?

**复杂任务(10+ 行 / schema 变更 / 跨多表)→ 4 段差集 + spec 文档**:

完整 spec 用 [`references/change-spec-template.md`](references/change-spec-template.md) 模板(AI 内部走清单,给用户看一段话总结)。4 段差集仍然要做,spec 是兜底用的内部文档。

**关键**:**4 段差集只用在"加 1-5 行"以上的任务**。改一格不要搞 4 段,显得啰嗦。

## 速查:三条命令

```bash
# A. 扫文件夹 + 同时拿到 patch JSON 骨架(强烈推荐)
# 注意:--output / --patch-template 都写成 <root>/xxx 这样的绝对路径,
# 不要只写文件名 —— 否则会落到 cwd 而不是用户的项目根。
python3 scripts/inspect_config_tables.py --root /path/to/config --format md --output /path/to/config/inventory.md --patch-template /path/to/config/patch.json

# B. 编辑 patch.json(填 updates / appends),格式见 references/patch-format.md
#    然后预览 + 生成副本(注意:--source 和 --output 必须是不同文件)
python3 scripts/patch_xlsx.py --source x.xlsx --output x_candidate.xlsx --patch patch.json --dry-run
python3 scripts/patch_xlsx.py --source x.xlsx --output x_candidate.xlsx --patch patch.json

# C. 对比 + 跨表引用对账
python3 scripts/diff_config_tables.py --source x.xlsx --candidate x_candidate.xlsx --output diff.md
# 带公式候选重算后:
python3 scripts/diff_config_tables.py --source x.xlsx --candidate x_candidate.xlsx --output diff.md --compare-formula-results
python3 scripts/validate_refs.py --workbook x_candidate.xlsx
```

带样例数据走查:`examples/walkthrough.md`。
patch JSON 格式参考:[`references/patch-format.md`](references/patch-format.md)。

## 操作原则

- **源表默认只读**。副本先行,覆盖只在用户明确点头之后。
- **源表含公式先停**。让用户决定转值、导出无公式版本,还是沿用公式;沿用时必须验算公式结果。
- **不发明**。不知道的字段、ID、引用,要么问,要么标 unknown。
- **项目原生工具 > 自带脚本**。项目自己的 `validate` / `build` / `export` 优先。
- **后入 AI 继承不审计**。`.ai-config-table/` / inventory / 项目本地 README / 表字段索引 已存在 → 先读再说话,不要在第一轮发"硬问题清单"或自组规则(详见 [`references/successor-rules.md`](references/successor-rules.md))。
- **沉淀 ≠ 同步**。skill 只管把项目记忆写到 `.ai-config-table/`;同步走 git / svn / 共享盘 / 邮件包 由团队定,**skill 不绑 VCS**(详见 [`references/multi-version-cross-repo.md`](references/multi-version-cross-repo.md))。
- **多版本项目先问版本**。看到 `trunk/` + `version_*/` 这种布局,先问"线上源是哪个 / 当前任务针对哪个版本",落到 `profile.md`,以后不再问;**没明示前不动 trunk**。
- **多行表头是常态**(中文名 / 英文字段 / 类型 / 注释)。inspect 会主动建议。
- **编码降级**:CSV / JSON 默认 UTF-8 解码失败自动尝试 GBK。
- **沙盒拒写 = 用户安全网**,不是要绕的障碍。

## 文件结构 + 安装

纯 Python + Markdown,无 MCP / 插件 / SaaS。Python 3.8+ 即可;`.xlsx` / `.xlsm` 还需要 `openpyxl`(`pip install -r requirements.txt` 或 `pip install openpyxl`)。CSV / TSV / JSON 用标准库。

- **Codex CLI**: `git clone https://github.com/1aita0v/ai-config-table-skill.git "${CODEX_HOME:-$HOME/.codex}/skills/ai-config-table"`
- **Claude Code(用户级)**: `git clone https://github.com/1aita0v/ai-config-table-skill.git ~/.claude/skills/ai-config-table`
- **Claude Code(项目级)**: `git clone https://github.com/1aita0v/ai-config-table-skill.git .claude/skills/ai-config-table`
- **Cursor / Aider / 其他**: 文件夹丢到 agent 看得见的地方,在 `.cursorrules` / `AGENTS.md` / `CLAUDE.md` 加一行指向 `ai-config-table-skill/SKILL.md`。

目录结构:
- `scripts/` —— inspect_config_tables / patch_xlsx / diff_config_tables / validate_refs / find_table / learn / _config_loader / _memory_locator / _pattern_summary。
- `references/` —— AI 按需打开的细则:rpg-config-patterns / patch-format / data-sources / no-data-source-report / project-profile-template / change-spec-template / validation-checklist / config-reference-playbook / profile-schema / sync-mechanisms / unknown-project-onboarding + 本次拆分新增的 successor-rules / multi-version-cross-repo / dialogue-samples / xlsx-roundtrip / windows-nonascii-paths / sandbox-writeback / learn-howto / full-pipeline / ambiguous-input。
- `examples/` —— 样例工作簿构建器 + 完整 walkthrough。
- `agents/openai.yaml` —— Codex / OpenAI 风格 skill 元数据。

## 反模式

- 没发现 + 没确认就直接改源表。
- 源表里还有公式时不确认用途就继续 patch,尤其是追加行 / 扩行数配置。
- 仅凭 ID 区间、文件名片段去推业务含义。
- 改主表不查本地化 / 资源 / 奖励 / 解锁条件。
- 把客户端 / 服务端生成产物当成"数据源真相"。
- 没具体路径 / 行 / 字段 / 证据 就说"验证通过"。
- 把 `references/` 模板当作业丢给用户填。
- 把 patch JSON 或 shell 命令贴给用户读。
- 想办法绕过运行环境的写保护去覆盖原表。

**多人 / 多版本 / 跨仓特有反模式**(完整清单见 [`references/successor-rules.md`](references/successor-rules.md) 和 [`references/multi-version-cross-repo.md`](references/multi-version-cross-repo.md) 末尾的反例段):
- 后入 AI 把项目本地约定 / 旧工具引用 / 包结构当成 skill bug 来 audit
- 多版本项目里不问版本就改 `trunk/`(★ trunk = 线上,高危)
- 跨版本 merge / 回流让 AI 自动做,而不是让用户走 VCS
- 把 `.ai-config-table/` 写在 SVN 自动同步镜像里(下次同步会丢)
- 默认 VCS 是 git,看到 svn / Dropbox 就建议改 git(★ skill 不绑 VCS)
