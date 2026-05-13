# 不熟悉的库接入 —— 完整流程

主 SKILL.md 给的是判定信号 + 分流表 + 6 步摘要。这里是详细命令模板、临时产物归属、触发词清单、对话样例和反例对照。

---

## 判定信号(完整)

**判定标准是 AI 对这个库的认知状态,不是用户嘴上说什么**。inspect 跑完之后:

- `<root>/.ai-config-table/` 不存在,或 inventory.md 开头 `## Project Memory` 段为空 → **AI 不认识这个库**
- 反之有内容 → **AI 已经认识**,按主 SKILL.md *完整流程* 章节走

用户的措辞只是初筛(见下面 *触发词粗筛*),最终看上面这个信号。

## 三种组合分流(完整说明)

| 用户带具体任务 | 库 AI 认识 | 怎么走 |
|---|---|---|
| 是 | 是 | 老流程:问表 → inspect → 改(见主 SKILL.md *完整流程* 章节) |
| 是 | 否 | **任务之前插一层**「先扫一眼,讲 **1-2 句**只跟这次改动相关的印象」(影响面 / 相关表),拿确认再动手 —— **不是把无任务接入的完整 6 步搬过来**,只讲服务于当下任务的 1-2 句 |
| 否 | 否 | **只读扫描 → 讲印象 → 问要不要入档**,到此结束(见下面 6 步) |
| 否 | 是 | 把 `## Project Memory` 念一遍,问「想看哪部分」/「今天要干啥」 |

**漂浮兜底**:用户说话很模糊、看不出带不带任务时(例:「你能帮我看看吗」「这堆 Excel 你能干啥」),**默认走「无任务接入」(只读)**,跑完印象再让用户加任务升级到老流程 —— **不要反过来**(不能先假设用户要改,然后等他纠正)。只读永远是安全选项。

## 不熟悉的库,6 步走

1. **告诉用户**:我先只读扫一遍,**不动你任何原文件**,完了讲一段印象。问路径。**例外**:用户只在问 capability(例:「你这玩意能干啥」「你能处理 Excel 吗」),先用一句话回答能力边界,**不要立刻进入扫描节奏** —— 等用户给路径或表达意图再开扫。

2. **跑 inspect**(顺手出 patch 骨架)。**`--output` / `--patch-template` 写到 root 所在目录**(root 是文件夹就是它本身;root 是单文件如 `sample.xlsx` 时是该文件的父目录),**不要只写文件名** —— Codex / Claude Code 的 cwd 通常不是用户的项目目录,直接写 `inventory.md` 会落到 skill 工作目录或临时目录里,用户找不到:

   ```bash
   # <root-dir> = root 所在目录(root 是文件夹时就是它自己;root 是单文件时是其父目录)
   python3 scripts/inspect_config_tables.py \
     --root <root> \
     --format md \
     --output <root-dir>/inventory.md \
     --patch-template <root-dir>/patch_template.json
   ```

   具体例子:
   - root 是 `~/myproj/cfg/` → `--output ~/myproj/cfg/inventory.md`
   - root 是 `~/myproj/cfg/sample.xlsx` → `--output ~/myproj/cfg/inventory.md`(**不是** `~/myproj/cfg/sample.xlsx/inventory.md`,后者是非法路径)

3. **读 inventory.md**(主要认知来源),给用户讲一段**口语化印象**,大致覆盖:
   - 识别到哪些文件、哪些 sheet
   - 哪几张看着像主表 / 文案表 / 奖励表(语气带「猜」)
   - 主表的表头行 / 数据起始行 / 主键候选
   - 几个样本值
   - **可能的跨表引用候选**(明确是猜,真正对账靠 `validate_refs`)
   - 推测的命名 / 结构规律,标「待用户确认」

4. **patch_template.json 是顺手出的骨架**,等用户下指令时直接填 —— **这一步只产生它,不讲给用户听**,避免把 JSON schema 抛给用户。

5. **用户确认/否决/补充后**,**问一次**:这些要不要写进 `<root-dir>/.ai-config-table/`,下次同项目我直接懂。用户说存才跑 `scripts/learn.py`(完整命令见主 SKILL.md *项目记忆* 章节,**不要重写命令**)。**用户说"不"/"先不存"/"算了" → 本轮到此结束,不要纠缠**(别再追问"那至少先记 inventory 路径吧"之类),也不要静默写到任何地方。

6. **不允许静默积累** —— 用户没说存就不写。

## 临时产物落哪里

`inventory.md` / `patch_template.json` 是临时扫描结果,**统一落在 root 所在目录**(root 是文件夹就是它本身,root 是单文件就是该文件的父目录)—— 和上面 6 步走第 2 步 inspect 命令的 `--output <root-dir>/inventory.md` 写法一致。**不要让它们落到 cwd**(Codex / Claude Code 的 cwd 通常不在用户项目里,用户找不到)。AI 复述时要**显式点名**这俩文件:

> `inventory.md` 和 `patch_template.json` 这俩刚生成的文件,你看完随时可以删。长期记忆在 `<root-dir>/.ai-config-table/`,而且必须你点头才写。

## Windows 中文路径

用户路径含中文时,提一句切到 `--config FILE` 模式,**详见主 SKILL.md *Windows + 非 ASCII 路径* 章节**(只引用,不在这里重抄命令)。

## 触发词粗筛(只是初筛,不是判据)

**正向**(可能不带任务接入):「装好了」「接入」「先熟悉」「帮我看看这个项目」「先扫一眼」
**反向**(带任务,走老流程):提到具体 ID / 字段 / 数值 / 增删改 / 加几行 / 改成 X

**最终判定看 `<root-dir>/.ai-config-table/` 状态,触发词只是初筛**。用户嘴上说「先熟悉」但 AI 已经认识这个库,就把 Project Memory 念一遍而不是再扫一遍。

## 对话样例(无任务接入,不熟悉的库)

> **用户**: 装好了,帮我接入这个项目的配置表
>
> **AI**: 好的。我先**只读扫一遍**,不动你任何原文件,扫完讲一段印象给你听。你的配置表在哪儿?给我一个文件夹路径。
>
> **用户**: `~/myproj/cfg/`
>
> **AI**: *(后台跑 `inspect_config_tables.py --root ~/myproj/cfg --format md --output ~/myproj/cfg/inventory.md --patch-template ~/myproj/cfg/patch_template.json`,自己读 inventory.md)*
>
> 扫完了,讲下印象 ——
>
> - 一共 7 个 Excel 文件、12 个 sheet。看着像主表的:`Item.xlsx`(道具)、`Skill.xlsx`(技能)、`Reward.xlsx`(奖励)。
> - `LocText.xlsx` 看着是**文案表**(字段 `LocKey / TextCN / TextEN`)。
> - `Item.xlsx` 前 4 行是表头(中文名 / 英文字段 / 类型 / 备注),数据从第 5 行开始,**主键我猜是 `ItemID`**(每行不同的整数)。样本:10001 Sword, 10002 Shield, 10003 Potion。
> - **跨表引用候选(猜)**:`Item.LocKey` → `LocText.LocKey`、`Reward.ItemID` → `Item.ItemID`。这俩还没真对账,真要用我跑 `validate_refs`。
> - 推测规律(**待你确认**):道具 ID 看着是 5 位数,1xxxx 段可能是装备类。
>
> 哪条对、哪条不对?另外这次过来想干啥?
>
> **用户**: 道具 ID 你猜的对,1xxxx 是装备。LocKey 那条对。Reward.ItemID 对,但 Reward 里还有 SkillID 也指 Item 不指 Skill,这个奇怪。今天先不改东西,就熟悉一下。
>
> **AI**: 收到,记下你纠正的 3 条:
> - 道具 ID 1xxxx = 装备 ✓
> - Item.LocKey → LocText.LocKey ✓
> - **Reward.SkillID → Item.ItemID(不是 Skill 表)** —— 这条反直觉,我自己肯定猜不到
>
> **要不要把这 3 条写进 `~/myproj/cfg/.ai-config-table/`,下次同项目我直接懂?**(写进去之前我什么都不会留,inventory.md / patch_template.json 这俩临时文件你看完也随时可以删。)
>
> **用户**: 写
>
> **AI**: *(跑 `learn.py` 3 次)* 写完了,3 条规律入档。下次你过来 inspect 一跑,这些规律会出现在 inventory.md 开头的 `## Project Memory` 段,我会自动应用。今天就到这,有事再叫我。

## 反例对照(带任务来,直接进老流程)

> **用户**: 把 10003 的品质改成 3
>
> **AI**: *(不要走熟悉分支 —— 用户带着具体 ID + 字段 + 数值来了)*
>
> 收到。我先 inspect 一下,然后给你 1 句话的计划。*(跑 inspect,读 inventory.md,看到 Project Memory 为空 —— 这是个不认识的库 + 带任务的情况,按上面表格走中间那行:**任务之前插一层先讲印象**)*
>
> 扫完了,简短讲下印象再动手:
>
> - `Item.xlsx` 4 行表头,主键 `ItemID`,10003 是 Potion(药水),当前品质 2。
> - 没看到其他表引用 Item.Quality 这个字段,改这一格不会牵动别的表。
>
> 计划:Item 表第 7 行(`10003 / Potion`),Quality `2 → 3`,其他不动。预览一下?

—— 注意区别:**带任务来的时候,印象段是 1-2 句服务于这次改动**(影响范围、相关表),**不展开念整个库**。无任务接入才走完整 6 步。
