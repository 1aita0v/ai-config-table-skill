# ai-config-table-skill

一个跨项目通用的 AI 能力包,让你的 AI 助手(Claude Code、Codex、Cursor)**安全地改你的配置表** —— Excel / CSV / TSV / JSON —— 在你点头之前,绝不动你的原文件。

无 MCP、无插件、无 SaaS,本质就是一个 Markdown + Python 的文件夹。

> 🌍 English: [README_en.md](README_en.md)

---

## 👤 给策划:你只看这一段就够

**装好之后**:

跟 AI 说人话,比如:

> 帮我把 `~/myproj/cfg/Item.xlsx` 里 10001 的品质改成 3

AI 会自动:**扫一遍 → 给你看预览 → 生成一个改后的副本(原文件不动)→ 摆出对比清单**。你看了 OK,说「覆盖」,AI 才会覆盖。

**你完全不用碰命令行,也不用看 JSON。** 下面的安装那一段是给程序员看的;装完之后正常跟 AI 对话就行。

担心 AI 改坏表?这个 skill 的核心承诺:
- 原文件**默认不动**,改动先去副本
- 任何复杂改动会先 dry-run 预览
- 公式 / 批注 / 合并单元格 / VBA 一般都会保留;数据验证下拉框、复杂条件格式、嵌入图表**可能会丢** —— 这种情况 AI 会主动告诉你,让你用 Excel / WPS 打开副本肉眼对比一次再覆盖。

---

## 它解决什么问题?

策划、PM、非程序员经常要管一堆 Excel / CSV 配置表(道具表、关卡表、奖励表、文本表)。今天直接让 AI "把 10001 这一行品质从 2 改成 3" 是危险的:

- AI 可能直接覆盖你的原文件,把下游搞坏
- AI 可能把列名认错,悄无声息地把某一行写坏
- AI 可能没注意到关联的另一张表(文本、图标)也得改,结果游戏里显示空白

这个 skill 给 AI 套了一个 **扫一遍 → 预览 → 生成副本 → 对比 → 你确认** 的流程。**AI 干活,你拍板**。

## 谁用得上?

- **策划 / PM** —— 手里有配置表,但不敢丢给 AI
- **程序员** —— 想给团队一个可复用、可审计的"AI 改配表"模式
- **任何人** —— 用 Claude Code、Codex、Cursor 等 agent CLI 处理表格

## 一段最小对话长什么样

```
你:  帮我把 ~/myproj/cfg/Item.xlsx 里 10003 的品质改成 3

AI:  找到了。10003 是 Potion(药水),当前品质 2。我会生成一个副本,
     只动这一格(标黄),原文件不动。要我先预览一下吗?

你:  好

AI:  预览:Item 表第 7 行(`10003 / Potion`),品质列,2 → 3,
     其他都不变。生成副本?

你:  生成

AI:  完成:~/myproj/cfg/Item_candidate.xlsx。对比下来只动了这一格。
     要我帮你覆盖回 Item.xlsx 吗?还是你自己拖过去?
```

---

## 安装(给程序员)

挑一条匹配你 agent 的命令:

```bash
# Codex CLI
git clone https://github.com/1aita0v/ai-config-table-skill.git "${CODEX_HOME:-$HOME/.codex}/skills/ai-config-table"

# Claude Code(用户级,所有项目都能用)
git clone https://github.com/1aita0v/ai-config-table-skill.git ~/.claude/skills/ai-config-table

# Cursor / Continue / Aider / 其他
git clone https://github.com/1aita0v/ai-config-table-skill.git ~/ai-config-table-skill
# 在项目规则文件(.cursorrules / AGENTS.md / CLAUDE.md)里加一行:
#   配置表相关的修改,请参考 ~/ai-config-table-skill/SKILL.md 的工作流。
```

装完就行。下次跟 AI 聊配置表它会自动激活(YAML 已经覆盖中英文触发词:"AI配表"、"改配置表"、"加一行"……)。

**前置条件**:Python 3.8+。改 `.xlsx` / `.xlsm` 需要 `pip install openpyxl`。CSV / TSV / JSON 标准库即可。

## 更新

```bash
cd ~/.claude/skills/ai-config-table   # 或你装的位置
git pull
```

`git tag --list` 看稳定点,`git checkout v1.2` 钉死某个版本。

## 包里有什么

- `SKILL.md` —— AI 跟着走的工作流,含对话样例和非程序员话术指南
- `scripts/` —— AI 跑的 Python 小脚本(扫描 / 改副本 / 对比 / **跨表引用对账**)
- `references/` —— AI 内部走流程用的模板和清单(不要丢给用户填)
- `examples/` —— 样例 Excel 构建器 + 完整 walkthrough
- `agents/openai.yaml` —— Codex / OpenAI 风格元数据

## Windows + 中文路径

Windows 默认代码页是 cp936,把中文路径作为命令行参数传给 Python 时,中间会丢字(`C:\TR\????\X.xlsx`)。这跟我们的脚本无关,是 Windows + agent 的 argv 编码问题。

**解决办法**:用 `--config FILE` 模式 —— 把参数写到 UTF-8 JSON 文件里,绕开 argv。`SKILL.md` 里已经写了完整规则,装好之后 AI 会自动按规则用。

脚本也会**主动检测路径里的 `?` 字符**,出问题时直接报清晰错误并列出修复步骤。

## 协议

MIT。详见 [LICENSE](LICENSE)。

## 发现 bug / 想要新功能

到 https://github.com/1aita0v/ai-config-table-skill/issues 开 issue —— 说清楚文件格式、你让 AI 做什么、它哪里做错了。
