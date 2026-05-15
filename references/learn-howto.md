# 项目记忆 (.ai-config-table/) —— 入档操作手册

**这一节只讲"怎么入档、什么时候入档、入档话术"**。落点规则 / 上溯逻辑 / 多版本布局 / 跨仓拓扑 / VCS 同步机制 / 跨人时序 → 见 [`multi-version-cross-repo.md`](multi-version-cross-repo.md) + [`profile-schema.md`](profile-schema.md) + [`sync-mechanisms.md`](sync-mechanisms.md)。

## Contents

- [`.ai-config-table/` 里有哪几个文件](#ai-config-table-里有哪几个文件)
- [入档的起点:inspect 的 "配表规律候选"](#入档的起点inspect-的-配表规律候选)
- [什么时候建议入档](#什么时候建议入档)
- [入档话术](#入档话术)
- [怎么入档 —— `learn.py` 一条命令](#怎么入档--learnpy-一条命令)
- [`项目档案.md`(跟 `项目规律.md` 平行的另一份记忆)](#项目档案md跟-项目规律md-平行的另一份记忆)

## `.ai-config-table/` 里有哪几个文件

| 中文名(新建用) | 老英文名(兼容) | 用途 |
|---|---|---|
| `项目规律.md` | `learned-patterns.md` | AI 学到的项目特有规则,**`learn.py` 写这个** |
| `项目档案.md` | `profile.md` | 项目级长期约定(路径锚点 / 多版本 / 写表入口),**AI 用 Read/Write 直接编辑** |
| `说明.md` | `README.md` | 目录用途说明,`learn.py` 首次新建时写一份 |

老项目已经有英文文件名(`learned-patterns.md` / `profile.md` / `README.md`)的,`learn.py` 会继续往老文件里 append,**不会出现新旧两份并存**;首次入档的新项目则用中文名。读取(inspect)对两种都认。

**铁律:任何累积都是用户明示同意后写入,绝不静默积累**。

## 入档的起点:inspect 的 "配表规律候选"

inspect 跑完后,inventory.md 会有一段 `## 配表规律候选(脚本扫出来的线索,未确认)`,自动扫出 8 类规律:

1. **数字主键 ID 段** —— 主键有明显段间跳跃(暗示业务分段)
2. **数组字段组** —— `Foo#1.Bar` / `Foo#2.Bar` 模式(改要整组改)
3. **跨 sheet 同名字段** —— 字段名在多 sheet 出现(项目级公共字段 / 外键)
4. **公式分布摘要** —— 哪些 sheet 有公式、top 5(公式闸门提示)
5. **隐藏列警示** —— 无 header 有数据的列(策划备注列,**严禁碰**)
6. **LocKey / 命名模板候选** —— string 字段匹配 `<Word>_<Word>_<digits>` 等
7. **重复 sheet 名警告** —— 同名 sheet 在多个文件(模糊指令时多确认)
8. **目录层级 / 业务分类** —— 子目录文件 / sheet 数 + `new/old/legacy/` 关键字 + 同名文件并存

**这些都标'猜'/'候选',AI 不能直接当事实用** —— 跟用户确认后才跑 `learn.py` 入档。已经在 `## Project Memory` 出现过的规律,候选会重叠 → 可跳过,优先看 Project Memory。

跑得慢或不想看可加 `--no-pattern-summary` 关掉(不建议,这是经验入档的最便宜入口)。

## 什么时候建议入档

任务跑完后,**主动问用户**(用户说"存"才存)。值得入档的信号:

- 稳定的 **命名规律**(LocKey 都是 `ITEM_<id>_NAME`、技能 ID 第 3 位代表槽位)
- 摸清的 **跨表引用约定**(Reward.ItemID → Item.ItemID、Skill.BuffID#N → Buff.BuffID)
- 用户 **否决** 过的判断(他说 X 不能这样改,要存下来下次别再问)
- **特殊字段** 含义(`AssetCode` 实际不是资源 id 而是分包代码,这种)

## 入档话术

**用户说"存"**:
> **AI**: 我注意到这个项目的 LocKey 都是 `ITEM_<id>_NAME` 格式 —— 要把这条记到 `.ai-config-table/` 里吗?下次加道具我就直接按这个生成,不再问你。
>
> **用户**: 存。
>
> **AI**: *(跑 `learn.py`)* 记下了。下次 inspect 一跑,这条会出现在 Project Memory 段,我自动应用。

**用户说"不存"** —— 立刻打住,**不许换个角度再问一遍**:
> **AI**: 那条命名规律,要记到 `.ai-config-table/` 吗?
>
> **用户**: 算了,下次再说 / 不用。
>
> **AI**: 好。本轮到此结束,**不再追问**。原文件没动过,临时 inventory 在那个目录,想留想删随你。

## 怎么入档 —— `learn.py` 一条命令

```bash
python3 scripts/learn.py \
  --root /path/to/config \
  --topic "lockey-rule" \
  --body "所有 LocKey 都是 ITEM_<id>_NAME 格式" \
  --evidence "Item 表 5 条已有数据全符合" \
  --apply-when "加新道具时直接按 ITEM_<新id>_NAME 生成,不再问用户"
```

落点逻辑(跟 inspect 读取完全一致,不会分裂):

- 默认沿 `--root` 向上找已存在的 `.ai-config-table/`(最多 3 层),找到就 append 进去
- 找不到 → 在 `<root>/.ai-config-table/` 新建 + 写 `说明.md` + 初始化 `项目规律.md`(老项目已有 `learned-patterns.md` 时继续往老文件 append)
- 跨仓拓扑 → 加 `--memory-root <工程仓>` 强制锁定
- stderr 打印实际落到哪个目录,对账方便

**`topic` 用稳定 slug**(英文小写 + 短横线),原因见 [`sync-mechanisms.md`](sync-mechanisms.md#跨人入档时序约定)。

## `项目档案.md`(跟 `项目规律.md` 平行的另一份记忆)

`项目档案.md`(老项目沿用 `profile.md`)装项目级长期约定(路径锚点 / 多版本布局 / 写表入口)。**没专门脚本**,AI 用 Read / Write 直接维护;inspect 自动把它整段塞进 Project Memory 段。

Schema + 字段说明 + 触发更新时机 → [`profile-schema.md`](profile-schema.md)。
