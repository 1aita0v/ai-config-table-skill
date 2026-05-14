# `profile.md` 最小 schema

`<工程仓>/.ai-config-table/profile.md` 是 AI 跟用户共编的"项目身份证"。`inspect_config_tables.py` 把它**整段 dump** 进 inventory 的 `## Project Memory` 段(不做结构化解析,**靠后入 AI 肉眼读**)。

下面是最低要写的字段。字段名照抄,值用户填(AI 跟用户共同编辑 / Read / Write 直接维护,没专门脚本)。

```markdown
# Project profile

## 路径锚点
- engineering_repo: /Users/.../my-game           # `<工程仓>` 绝对路径(.codex / AGENTS.md 同级)
- config_root: /Users/.../my-game/data/configs   # `<配置仓>` —— inspect 的 --root 该传这个
- external_config_root: /Users/Shared/...        # ★ 跨仓拓扑才填:配置源不在工程仓内时

## 多版本布局(无多版本就不写这段)
- baseline: <配置仓>/trunk/                      # 线上源,diff 的基准
- current_version: <配置仓>/version_1.1/         # 当前主要在改的版本
- known_versions:
    - <配置仓>/version_1.0/   (已上线,等回归)
    - <配置仓>/version_1.2/   (规划中)

## 写表入口(并行工具记一下,避免后入 AI 误判)
- skill: scripts/patch_xlsx.py                   # ai-config-table-skill 自带
- team:  .codex/tools/write_xlsx.py              # 团队自家(可选,有就记)
```

## 字段说明

- 占位符 `<工程仓>` / `<配置仓>` 是**写给人看的提示**,实际值用绝对路径。
- inspect 默认把这个文件原文塞进 Project Memory 段;后入 AI **自己读懂上面字段**,不靠工具解析。
- `external_config_root` 存在 → 提示后入 AI 跑 inspect 时用 `--memory-root <工程仓>`(或读 profile.md 后用脚本自动加上)。
- "写表入口"段不强制,但项目有团队自家写表工具(平行于 `scripts/patch_xlsx.py`)时**强烈推荐记一下**,避免后入 AI 把它当成"旧引用"误删或忽略。

## 触发更新 profile.md 的时机

- 首次跨仓接入:用户告诉你 `<工程仓>` 在哪、`<配置仓>` 在哪 → 写下 `engineering_repo` / `config_root` / `external_config_root`
- 多版本项目首次接入:用户告诉你哪个是线上源、当前在改哪个版本 → 写下 `baseline` / `current_version` / `known_versions`
- 发现团队有平行写表工具:`ls` 验证存在后 → 写下 `team:` 一行

每次写都问用户"要不要存到 profile.md",**不静默写**。
