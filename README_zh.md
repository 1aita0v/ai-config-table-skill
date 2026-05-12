# ai-config-table-skill

一个跨项目通用的 AI 能力包,让你的 AI 助手(Claude Code、Codex、Cursor,或任何能跑 Python 3.8+ 的 agent)**安全地改你的配置表** —— Excel / CSV / TSV / JSON —— 在你点头之前,绝不动你的原文件。

无需 MCP、无需插件、无需 SaaS,本质就是一个 Markdown + Python 的文件夹。

## 它解决什么问题?

策划、PM、非程序员经常要管一堆 Excel / CSV 配置表(道具表、关卡表、奖励表、文本表)。今天让 AI "把 10001 这一行的品质从 2 改成 3" 是危险的:

- AI 可能直接覆盖你的原文件,把下游的东西搞坏。
- AI 可能把列名认错,悄无声息地把某一行写坏。
- AI 可能没注意到关联的另一张表(文本、图标)也得改,结果游戏里显示空白。

这个 skill 给 AI 套了一个 **扫一遍 → 预览 → 生成副本 → 对比 → 你确认** 的流程。**原文件在你明确点头之前不会被动**。AI 干活,你拍板。

## 谁用得上?

- **策划 / PM** —— 手里有配置表,但不敢把它丢给 AI。
- **程序员** —— 想给团队一个可复用、可审计的"AI 改配表"模式,跨项目通用。
- **任何人** —— 用 Claude Code、Codex、Cursor 等 agent CLI 处理表格类配置。

你 **不需要** 懂 Python、JSON 或命令行。所有命令都是 AI 跑,你只需要用大白话告诉它你想做什么。

## 安装

挑一条匹配你 agent 的命令:

```bash
# Codex CLI
git clone https://github.com/1aita0v/ai-config-table-skill.git "${CODEX_HOME:-$HOME/.codex}/skills/ai-config-table"

# Claude Code(用户级,所有项目都能用)
git clone https://github.com/1aita0v/ai-config-table-skill.git ~/.claude/skills/ai-config-table

# Cursor / Continue / Aider / 其他
git clone https://github.com/1aita0v/ai-config-table-skill.git ~/ai-config-table-skill
# 然后在你的项目规则文件(.cursorrules、AGENTS.md、CLAUDE.md)里加一行:
#   配置表相关的修改,请参考 ~/ai-config-table-skill/SKILL.md 的工作流。
```

装完就行。下次你跟 AI 聊到配置表,它会自动用上(`SKILL.md` 顶部的 YAML `description` 已经覆盖了常见的触发词:"AI配表"、"读配置表"、"改配置表"、"加一行"、"批量改"……)。

**前置条件**:Python 3.8+。改 `.xlsx` / `.xlsm` 需要 `pip install openpyxl`。CSV / TSV / JSON 用 Python 标准库即可。

## 一段最小对话长什么样

```
你:  帮我把 ~/myproj/cfg/Item.xlsx 里 10001 的品质改成 3

AI:  找到了。10001 是 Sword(剑),当前品质 2。我会生成一个副本,
     只动这一格(标黄),原文件不动。要我先预览一下吗?

你:  好

AI:  预览:Item 表第 5 行(就是 `10001 / Sword` 那一行)的品质列,
     2 → 3,其他都不变。生成副本?

你:  生成

AI:  完成:~/myproj/cfg/Item_candidate.xlsx。对比下来只动了这一格。
     要我帮你把它覆盖回 Item.xlsx 吗?还是你自己拖过去?
```

## 更新

我后续如果改了东西,你跑一句就拿到新版本:

```bash
cd ~/.claude/skills/ai-config-table   # 或者你装的位置
git pull
```

Tag 标记的是稳定点(`git tag --list` 查看)。想钉死某个版本用 `git checkout v1.0`。

## 包里有什么

- `SKILL.md` —— AI 跟着走的工作流,含对话样例和"如何跟非程序员对话"的指南。
- `scripts/` —— 三个 AI 会自己跑的 Python 小脚本(扫描 / 改副本 / 对比)。
- `references/` —— AI 会填的模板和清单。
- `examples/` —— 一个生成的示例 Excel + 完整 walkthrough。
- `agents/openai.yaml` —— Codex / OpenAI 风格的 skill 元数据。

## 协议

MIT。详见 [LICENSE](LICENSE)。

## 发现 bug 或想要新功能?

到 https://github.com/1aita0v/ai-config-table-skill/issues 开 issue —— 说清楚你的文件格式、你让 AI 做什么、它哪里做错了。
