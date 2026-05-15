# 用户给的信息模糊怎么办

主 SKILL.md 简单 case 直通车里有钩子:用户描述模糊("世界 boss 那张表" / "ConditionExtra 啥意思")时打开本文件。

非常常见。两类:**说不清哪张表** 和 **字段不懂含义**。两个都不许直接猜,也不要直接抛回去问"哪张表?" / "这字段啥意思?" —— 用户嫌烦,你显得没用。

**统一原则:先用你手里的数据找证据,带着证据再问**。

## Contents

- [A. 用户说不清哪张表](#a-用户说不清哪张表例去世界-boss那张冒险表商店那个)
- [B. 字段不懂含义](#b-字段不懂含义例conditionextracoefficientassetcode)
- [学到了就入档](#学到了就入档)

## A. 用户说不清哪张表(例:"去世界 boss"、"那张冒险表"、"商店那个")

3 步:

1. **inventory grep**:用 `scripts/find_table.py` 跑关键词搜索(对照 sheet 名 / file 名 / 字段名 / 样本值,自动排序):

   ```bash
   # 先 inspect 拿 JSON 清单(如果还没跑过)
   python3 scripts/inspect_config_tables.py --root /path/to/config --format json --output /tmp/inv.json
   # 再搜
   python3 scripts/find_table.py --inventory /tmp/inv.json --keyword "boss,世界,WorldBoss"
   ```

   输出按相关度列前 5 个候选,带"为什么匹配上的"。

2. **看项目记忆**:`<root>/.ai-config-table/` 里有没有用户之前教过的"这个项目的 X 在哪儿"。

3. **带候选列表问** —— 不要空问"哪张表",要列具体候选:

   > 我在你项目里搜到 3 张可能相关:
   > - `WorldHunting.xlsx` → `BossHunting` sheet(字段含 `BossID / IsWorldBoss`)
   > - `Adventure.xlsx` → `WorldBoss` sheet(字段含 `Difficulty / Reward`)
   > - `Activity.xlsx` → `Boss` sheet
   >
   > 你说的是哪张?或者直接告诉我文件路径。

## B. 字段不懂含义(例:"ConditionExtra"、"Coefficient"、"AssetCode")

5 个证据来源,**挨个查再问**:

| 证据 | 怎么用 |
|---|---|
| **inspect sample** | 拉 3-5 行实际值。`1,1` / `0,0`?百分数?ResId 引用?值就在暗示含义 |
| **meta_rows(注释行)** | 多行表头里通常有一行写策划注释。`field_row=2 meta_rows=[1,3,4]` 的 4 就是 |
| **跨 sheet 同名字段** | 这个字段在其他 sheet 是不是也出现过?那张表的样本 / 注释清不清楚 |
| **`.ai-config-table/项目规律.md`**(老项目 `learned-patterns.md`) | 项目记忆里有没有人记过这个字段 |
| **RPG 反模式 1**([`rpg-config-patterns.md`](rpg-config-patterns.md)) | 是不是 ID 段字段?有没有独立业务字段才是真相 |

**带证据问** —— 不要空问"这字段啥意思":

> `ConditionExtra` 我看了 5 行样本,值都是 `1,1` / `0,0` 这种两位整数对。第 4 行备注写"触发参数"。看着像 `(参数1, 参数2)` 格式,但具体含义没明确文档。
>
> 你能确认:
> - 这是 (参数1, 参数2) 还是单值?
> - 1 和 0 分别什么意思?
> - 我这次要配的新条目,应该填什么?

具体、有锚点、可直接答 —— 比"这个字段啥意思?"好用 10 倍。

## 学到了就入档

用户答了之后,**主动问"要不要存档?"**。用户说存就跑 `scripts/learn.py`(详见 [`learn-howto.md`](learn-howto.md)),下次同项目不再问。
