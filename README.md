# ai-config-table-skill

[![License: MIT](https://img.shields.io/github/license/1aita0v/ai-config-table-skill)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![Latest tag](https://img.shields.io/github/v/tag/1aita0v/ai-config-table-skill?label=release)](https://github.com/1aita0v/ai-config-table-skill/tags)

让 AI agent(Claude Code、Codex、Cursor 等)**安全地编辑 Excel / CSV / TSV / JSON 配置表** —— 原文件永远先做副本和 diff,覆盖前必须用户明确确认。

无 MCP、无插件、无 SaaS,只是一份 Markdown + 几个 Python 脚本。

> Available in [English](README_en.md).

---

- **如果你是策划 / PM**:安装由开发完成。装好之后用自然语言告诉 AI 改哪张表的哪一行就行;AI 会生成副本、出预览、等你确认再覆盖。完整对话示例见 [`SKILL.md`](SKILL.md)。
- **如果你是开发**:继续往下看。

## 它解决什么问题

策划手里有大量 Excel / CSV 配表(道具、关卡、奖励、文案),直接让 AI 改原文件有三个常见风险:

1. AI 把原文件覆盖了,下游构建挂掉
2. AI 把列名认错,某一行被静默写坏,几天后才被发现
3. 关联表(文案、图标)忘了同步,运行时显示空白或断言
4. 表里临时公式没清,追加行 / 扩行数后公式算错但没人发现

这个 skill 把 AI 套进一条 **扫描 → 公式闸门 → 预览 → 副本 → 对比 → 用户确认** 的固定流程,让"AI 干活、人拍板"成为默认行为,而不是靠 prompt 提醒。

## 工作流

```
inspect        →  formula gate     →  patch (dry-run)  →  patch          →  diff             →  validate_refs
扫描配表目录      有公式先确认处理      预览将要改的格子      复制源、改副本     对比源 vs 副本     跨表外键(orphan)校验
出 inventory     转值或明确沿用        不写盘              改动的格子标黄     按 sheet 列改动    候选发布前最后兜底
+ patch 骨架      沿用时验算结果
```

每一步都是一个独立 Python 脚本,失败原子化(出错就退出,不留半截产物)。AI 跟着 `SKILL.md` 的工作流串起来,用户在"实际生成副本"和"覆盖回去"两个节点参与决策。

## Quickstart(5 分钟在本地试一遍)

```bash
git clone https://github.com/1aita0v/ai-config-table-skill.git
cd ai-config-table-skill
pip install openpyxl

# 生成样例工作簿(模拟典型游戏配表:多行表头 + 文案表 + 奖励表)
python3 examples/build_sample.py

# 跑完整流程
python3 scripts/inspect_config_tables.py --root examples/sample.xlsx --format md --output inventory.md --patch-template patch.json
python3 scripts/patch_xlsx.py     --source examples/sample.xlsx --output examples/sample_candidate.xlsx --patch examples/sample-patch.json --dry-run
python3 scripts/patch_xlsx.py     --source examples/sample.xlsx --output examples/sample_candidate.xlsx --patch examples/sample-patch.json
python3 scripts/diff_config_tables.py --source examples/sample.xlsx --candidate examples/sample_candidate.xlsx --output diff.md
python3 scripts/validate_refs.py  --workbook examples/sample_candidate.xlsx
```

带逐步说明、预期输出、清理命令的完整版本见 [`examples/walkthrough.md`](examples/walkthrough.md)。

## 安装到你的 agent

挑一条匹配你的 agent CLI:

```bash
# Codex CLI
git clone https://github.com/1aita0v/ai-config-table-skill.git "${CODEX_HOME:-$HOME/.codex}/skills/ai-config-table"

# Claude Code(用户级,所有项目都可用)
git clone https://github.com/1aita0v/ai-config-table-skill.git ~/.claude/skills/ai-config-table

# Cursor / Continue / Aider / 其他
git clone https://github.com/1aita0v/ai-config-table-skill.git ~/ai-config-table-skill
# 然后在项目规则文件(.cursorrules / AGENTS.md / CLAUDE.md)里加一行:
#   配置表相关的改动请按 ~/ai-config-table-skill/SKILL.md 的工作流执行。
```

安装后 skill 会被对应 agent 自动激活 —— YAML 触发词覆盖中英文常见表达(`AI配表` / `改配置表` / `加一行` / `change config table` …)。

## 包内结构

| 路径 | 作用 |
|---|---|
| [`SKILL.md`](SKILL.md) | AI 跟着走的工作流主文档:决策点、对话样例、差集分级、平台兼容、项目记忆 |
| [`scripts/inspect_config_tables.py`](scripts/inspect_config_tables.py) | 扫描配表目录,生成 `inventory.md` 和 `patch.json` 骨架 |
| [`scripts/patch_xlsx.py`](scripts/patch_xlsx.py) | 复制源到副本,按 patch JSON 改动并把改过的格子标黄;支持 `--dry-run` |
| [`scripts/diff_config_tables.py`](scripts/diff_config_tables.py) | 对比源和副本,按 sheet 列出值差异和公式变化;带公式流程可加 `--compare-formula-results` 对比重算后的缓存结果 |
| [`scripts/validate_refs.py`](scripts/validate_refs.py) | 跨表外键(orphan)校验,自动检测 `Item.LocKey → LocText.LocKey` 这类引用 |
| [`scripts/find_table.py`](scripts/find_table.py) | 按关键词在 inventory 里搜 sheet 和字段(用户描述模糊时定位) |
| [`scripts/learn.py`](scripts/learn.py) | 把用户确认过的字段含义、约定写入 `<config-root>/.ai-config-table/` 项目记忆 |
| [`references/`](references/) | AI 内部走流程时引用的模板和清单(patch JSON 格式、字段含义证据来源、RPG 配表心智模型、发布前 checklist 等) |
| [`examples/walkthrough.md`](examples/walkthrough.md) | 完整 walkthrough,跑在自动生成的样例工作簿上 |
| [`agents/openai.yaml`](agents/openai.yaml) | Codex / OpenAI 风格 agent 元数据(skill 激活配置) |

## 兼容性

- **Python**:3.8+
- **平台**:macOS / Linux / Windows
- **xlsx / xlsm 编辑**:需要 `pip install openpyxl`
- **CSV / TSV / JSON**:Python 标准库即可

Windows 默认代码页是 cp936/GBK,把含中文的路径作为命令行参数传给 Python 时容易丢字(`C:\TR\????\X.xlsx`)。所有脚本都支持 `--config FILE` 模式,把参数写到 UTF-8 JSON 里绕开 argv 编码;脚本也会主动检测路径里的 `?` 字符并报清晰错误。完整规则见 `SKILL.md` 的 "Windows + 非 ASCII 路径" 段。

## 版本

`git tag --list` 查看历史版本,`git checkout v1.x` 钉死某个版本。当前版本系列(v1.x → v2.x)主要差异:

- **v2.x** 引入模糊输入处理、4 段差集分级、`find_table` 搜索
- **v1.7** 引入项目记忆(`<config-root>/.ai-config-table/`)
- **v1.5+** 完整 Windows + 非 ASCII 路径兼容
- **v1.4** 备注列、依赖钉版本、写盘 fallback

每个版本的具体改动见对应 commit message。

## 更新

```bash
cd ~/.claude/skills/ai-config-table   # 或你装的位置
git pull
```

## 许可证

MIT。详见 [LICENSE](LICENSE)。

## 反馈

Bug 报告 / 功能建议:[GitHub Issues](https://github.com/1aita0v/ai-config-table-skill/issues)。请附文件格式、给 AI 的指令、以及实际行为与预期的差异。
