# 对话样例

下面 7 段中文 + 1 段英文,示范 **对话的形状**,具体措辞按用户语气调整。主 SKILL.md 留了样例 2(最常用)做内置锚点,其它在这里。

## Contents

- [样例 1 — 用户给一个文件夹路径](#样例-1--用户给一个文件夹路径)
- [样例 2 — 用户想改一个值(主文档内置)](#样例-2--用户想改一个值主文档内置)
- [样例 3 — 用户加新行(跨表引用风险)](#样例-3--用户加新行跨表引用风险)
- [样例 4 — 用户不知道结构怎么回答](#样例-4--用户不知道结构怎么回答)
- [样例 5 — 用户想跳步骤](#样例-5--用户想跳步骤)
- [样例 6 — 用户说不清哪张表(用 find_table)](#样例-6--用户说不清哪张表用-find_table)
- [样例 7 — 字段不懂含义(5 个证据来源 + 带证据问)](#样例-7--字段不懂含义5-个证据来源--带证据问)
- [Dialogue (English flavor)](#dialogue-english-flavor)

## 样例 1 — 用户给一个文件夹路径

> **用户**: 帮我看下我配置表里 Item 表的 10001 是什么
>
> **AI**: 好,你的配置表在哪儿?给我一个文件夹路径,或者直接把 Excel 文件拖给我。
>
> **用户**: `~/myproj/cfg/`
>
> **AI**: *(后台跑 inspect,自己读结果)* 找到了。`Item.xlsx` 前 4 行是表头(中文名 / 英文字段 / 类型 / 备注),数据从第 5 行开始。10001 这一行是:Sword(剑),描述 "A basic sword.",图标 `icon_sword`,品质 1。要改什么?

## 样例 2 — 用户想改一个值(主文档内置)

主 SKILL.md 已经留了这段做内置锚点,这里不重复。

## 样例 3 — 用户加新行(跨表引用风险)

> **用户**: 帮我加 5 个新道具进 Item 表,ID 从 10020 开始
>
> **AI**: 没问题。这种加新道具的事,通常配套要做的事不少 —— 文本表里的中文名、图标资源表里的对应条目,如果只加 Item 不加这些,游戏里可能显示空白。在你给我中文名图标之前,我先把工作分两部分:
>
> - **你来定**:5 个道具的中文名、描述、图标资源名 / 路径
> - **我来核**:ID 10020-10024 这段没被占用、文本表(LocText 这种)和图标表的格式
>
> 你把中文名图标发我,我扫完就告诉你后续要不要补哪几张表。

## 样例 4 — 用户不知道结构怎么回答

> **用户**: 不知道,你看着办
>
> **AI**: OK 我先看一眼,5 秒。*(跑 inspect)* 看完了。Item 表第 1 行是中文(物品ID / 名称 / 描述 …),第 2 行是英文字段名(ItemID / Name / Desc …),第 3 行是类型,数据从第 5 行开始 —— 这种 4 行表头很常见,我按这个理解处理。唯一 ID 是 `ItemID`,我用它定位行。继续?

## 样例 5 — 用户想跳步骤

> **用户**: 直接帮我把改完的文件覆盖回去就行,别给我看什么副本了,麻烦
>
> **AI**: 副本和 diff 是这工具的底线 —— 没有它们我一旦改错没法救,所以这两步省不掉,但 **我可以把它们压成一句话**:我生成 `X_candidate.xlsx`,然后用一句话告诉你改了哪几格。你看着对就一个字 OK,我再覆盖回原文件;不对你说哪不对,我改 patch 重来。**覆盖前必须你点头**。这样既不绕路,也不会把你原文件改坏。

## 样例 6 — 用户说不清哪张表(用 find_table)

> **用户**: 帮我看下世界 boss 那张表的奖励配置
>
> **AI**: *(后台跑 inspect + find_table,关键词 "boss,世界,WorldBoss")*
>
> 你项目里跟"世界 boss"相关的我搜到 3 张:
>
> 1. `WorldHunting.xlsx` → `BossHunting` sheet(字段含 `BossID / RewardMax#1.PropID / RewardMax#1.Value`,看起来是主目标)
> 2. `Adventure.xlsx` → `WorldBoss` sheet(字段含 `Difficulty / Reward`)
> 3. `Activity.xlsx` → `Boss` sheet(只匹配关键词 "boss",可能是普通 boss 不是世界 boss)
>
> 你说的是 1 还是 2?或者你直接告诉我文件名 / 路径。
>
> **用户**: 1
>
> **AI**: 收到。`WorldHunting.xlsx` 的 `BossHunting` sheet,奖励字段是 `RewardMax#1` / `#2` / ...(数组形式)。你要看几条样本,还是直接说要改什么?

## 样例 7 — 字段不懂含义(5 个证据来源 + 带证据问)

> **用户**: 帮我把所有 `ConditionExtra` 是 `1,1` 的改成 `0,0`
>
> **AI**: *(查 sample / meta_rows / 跨 sheet / 项目记忆)*
>
> `ConditionExtra` 这个字段我看了证据:
>
> - **5 行样本**: 值都是 `1,1` 或 `0,0` 这种两位整数对
> - **第 4 行备注** 写的是"触发参数"
> - **同名字段在 Buff 表里也有**,那张表注释更清楚:"层数堆叠模式: 1,1=堆叠累计 / 0,0=独立重置"
> - **`.ai-config-table/` 项目记忆**: 没记过这个字段
>
> 我推测这个字段是"层数堆叠模式",`1,1`=堆叠 / `0,0`=独立重置。
>
> 你确认下:
> - 我的推测对吗?
> - "所有 `1,1` 改成 `0,0`"是把所有堆叠模式都改成独立重置?这样改影响范围比较大,你确认是想全改?
> - 改完要不要顺手在 `.ai-config-table/` 记一下这个字段的含义,下次同项目我直接懂?
>
> **用户**: 推测对,但只改 SkillID 在 1000-2000 范围的,其他不动。记下字段含义。
>
> **AI**: 收到。范围限定 + 字段含义入档。*(继续走 4 段差集 → dry-run → 生成 → ...)*

## Dialogue (English flavor)

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
