---
name: ai-config-table
description: >-
  Portable AI workflow for safely editing project configuration tables — Excel,
  CSV, TSV, JSON, exported workbooks, cloud sheets, or platform table APIs.
  Activate when the user asks to inspect, document, change, patch, add rows,
  batch-edit, validate, or review config data. Also triggers on Chinese
  phrasing: 改配置表, AI 配表, 加一行, 批量改, 配表复核, 跨表引用校验.
  Works under Claude Code, Codex, Cursor, or any agent that can run
  Python 3.8+ and read this directory.
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

用户用什么语言写,你就用什么语言回。下面对话样例多数是中文(原始受众),最后有一个英文样例做锚点 —— 其他语言按同样思路适配。

工作流(inspect → 副本 → diff → 用户确认)本身与语言无关。

## 这个 skill 在做什么(6 步)

1. **问** —— 表在哪、什么格式、表头几行,不要猜。
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

**下面这些章节只在以下信号出现时打开**:

| 触发信号 | 打开这节 |
|---|---|
| `.ai-config-table/` 已存在(你不是第一个 AI) | *[后入者守则](#你不是第一个-ai-时--后入者守则)* |
| 项目根有 `trunk/` + `version_*/` 多版本布局 | *[多版本配置管理](#多版本配置管理项目有-trunk--version_-这种布局时)* |
| 配置源在外部 SVN、工程仓是 git(GameDevelop 形态) | *[跨仓拓扑](#跨仓拓扑配置源在-svn工程仓在-git-gamedevelop-形态)* |
| 用户描述模糊("世界 boss 那张表" / "ConditionExtra 啥意思") | *[用户给的信息模糊怎么办](#用户给的信息模糊怎么办)* |
| Windows + 中文路径报错 | *[Windows + 非 ASCII 路径](#windows--非-ascii-路径中文目录名--用-config-模式)* |
| 沙盒拒绝覆盖原表 | *[沙盒不让你覆盖原表怎么办](#沙盒不让你覆盖原表怎么办--别绕交给用户)* |

简单 case 直走 6 步,**不要先去读"后入者 / 多人 / 多版本"那一长段**,会浪费时间。

## 遇到不熟悉的配置库时

**判定信号(看 AI 对库的认知状态,不是用户的轮次)**:
- `<root-dir>/.ai-config-table/` 不存在,或 inventory.md 开头 `## Project Memory` 段为空 → **AI 不认识这个库**
- 有内容 → **AI 已经认识**(走主文件 *完整流程* 章节)

> `<root-dir>` = root 所在目录:root 是文件夹时就是它自己;root 是单个文件(如 `sample.xlsx`)时是其父目录。本文档全部约定如此。

用户措辞(「装好了」「先熟悉」「直接改 X」等)只是初筛,最终看上面这个信号。

### 分流(4 种组合)

| 用户带具体任务 | 库 AI 认识 | 怎么走 |
|---|---|---|
| 是 | 是 | 老流程:问表 → inspect → 改(见 *完整流程* 章节)。**先读 [*后入者守则*](#你不是第一个-ai-时--后入者守则) —— 你不是第一个 AI** |
| 是 | 否 | **任务之前插一层** 1-2 句只跟改动相关的印象(影响面 / 相关表),拿确认再动手 —— **不是把无任务接入的完整 6 步搬过来** |
| 否 | 否 | **只读扫描 → 讲印象 → 问要不要入档**,到此结束(见下方 6 步) |
| 否 | 是 | 把 `## Project Memory` 念一遍,问「想看哪部分」/「今天要干啥」。**先读 [*后入者守则*](#你不是第一个-ai-时--后入者守则)** |

**漂浮兜底**:用户说话模糊、看不出带不带任务时(「你能帮我看看吗」),**默认走「无任务接入」(只读)**,跑完印象再升级到老流程 —— **不要反过来**。只读永远是安全选项。

### 不熟悉的库,6 步摘要

1. **告诉用户只读扫一遍,不动原文件,问路径**。例外:用户只在问 capability(「你这玩意能干啥」)→ 先答能力边界,**不立刻扫**。
2. **跑 inspect**,`--output` / `--patch-template` 写成绝对路径 —— **临时产物落 `/tmp/<某子目录>/`**(或系统 temp),不要落用户项目里(避免污染镜像 / 双向同步盘 / build 目录)。`cwd` 通常不在用户项目里,只写文件名会落到错位置。
3. **读 inventory.md,口语化讲印象**:文件/sheet/主键/跨表引用候选/推测规律(都标"猜")。
4. **patch_template.json 是骨架**,等用户下指令时再用,不讲给用户听。
5. **问一次是否入档**。落点按 *[Layer 2 落点判断](#layer-2-落点判断--vcs-无关)* 章节走 —— 默认 `<工程仓>/.ai-config-table/`(`learn.py` 自动找上溯 3 层内已存在的,找不到才在 `<root>` 新建)。用户说存才跑 `scripts/learn.py`(见 *项目记忆* 章节)。用户说"不"/"先不存"/"算了" → **本轮结束,不纠缠、不静默写**。
6. **不允许静默积累**。

**详细命令模板、临时产物归属、触发词清单、对话样例、反例对照,见 [`references/unknown-project-onboarding.md`](references/unknown-project-onboarding.md)。**

### 普通三件事问法(库 AI 已经认识时用)

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

如果用户根本没法给数据源 —— 用 `references/no-data-source-report.md` 写一份「找不到数据源」报告,然后**停下**。不要瞎编表名、ID、规则。

## 你不是第一个 AI 时 —— 后入者守则

skill 提供的脚本路径和工作流是固定的,但**项目本地规范不是 skill 决定的** —— 每个项目有自己的文件夹布局、命名约定、内部知识库,以及可能已迁移走的旧工具引用。后入 AI 的本分是**继承现状、用 skill 入口干活、在现状基础上优化**,**不是审计现状**。

**判定信号**(满足任一条 → 你是后入 AI):

- `<root-dir>/.ai-config-table/` 已存在,inventory.md 开头 `## Project Memory` 段非空
- 项目根有团队自己的 README / 表字段索引 / 内部知识库,引用了具体表 / 字段 / 工具名(包括可能已迁移走的旧工具)
- 用户语气是「接着上次」「按之前的规矩」「按某某文档继续」

### 3 条守则

**1. 先继承,后开口** —— 读完 SKILL.md、`<root-dir>/.ai-config-table/`、项目根的 README / 表字段索引 / 内部知识库,**再开始说话**。第一轮不要总结"我会默认遵守 A / B / C / D" —— 那一定是没读全,等于浪费用户一轮。

**2. 本地规范是事实,不是 bug** —— 项目自己的文件夹布局(可能有 `tools/` / `develop/` / `config/`)、命名约定、旧工具引用,**不审计、不"修正"**。

举例:项目 README / 表字段索引提到 `tools/write_xlsx.py` —— 这有两种可能,**你不预设哪种**,先 `ls` 验证再决定:
- (a) 旧文档残留,工具已迁移走 → 用 skill 的 `scripts/patch_xlsx.py` 顶替
- (b) **团队自己的并行写表工具**,跟 skill 的 `scripts/patch_xlsx.py` **平行存在** → 两者都能用,具体走哪个听用户当下指令(团队工具可能产出团队特定格式 / 标记;skill 工具更通用)

skill 入口 vs 项目目录规范 —— **两边都遵守,不互相覆盖**。两个写表工具同时活的话也是。

**3. 优化,不重做** —— skill 包结构是稳定的:

- `scripts/*.py` × 7(inspect / patch_xlsx / diff / validate_refs / find_table / learn / _config_loader)
- `references/*.md` × 9
- `SKILL.md` + `README.md` + `README_en.md`
- `agents/openai.yaml`(7 行触发元数据,**不是工作流文档**)

不一致时 `ls scripts/ references/` 对齐一次就翻篇。**不要**把"我扫到几个文件名错位 / .py 内容不对劲 / 真正 workflow 在 yaml" 当成有效产出 —— 那是审计噪音,不是产出。

你的产出永远是**「在现状基础上,下一步具体动作」**(下一个改表任务 / 下一条入档建议 / 下一步验证),不是"现状审计清单"。

### 第一句话该说什么 —— 正例 vs 反例

读完 SKILL.md + `.ai-config-table/` + 本地 README,**第一句话只点本次任务相关的继承,然后直奔任务**。

✓ **正例**(用户说"改 10001 品质 2 → 3"):
> 我看了项目记忆,这次改 Quality 列,跟 col2 备注列没关系,col2 我不会动。10001 品质 2 → 3,先 dry-run 给你看?

✗ **反例 1**(自组规则清单):
> 我已按这个 skill 完成只读接入。后续我会默认遵守:① 原 Excel 只读 ② 先锁主表 ③ 联查 I18N / Item / Resource ...

✗ **反例 2**(假装第一次接入,装作不知道):
> 你的配置表在哪儿?给我一个文件夹路径 ...

正例的形状:**一句话证明读过项目记忆**(只点跟本次任务相关的、能引发风险的那 1-2 条)+ **马上进任务动作**(dry-run / 三件事问法 / 找文件)。

### 反例 —— 看到自己写下面这种立刻停

- "你传来的包文件名错位 / 几个 .py 内容不对劲"(包结构稳定,ls 自己对齐)
- "知识库里的 `tools/X` 没找到"(可能是旧引用,也可能是并行活工具,**先 ls 验证再下结论**)
- "真正的 workflow 在 `agents/openai.yaml`"(不,SKILL.md 才是;yaml 是 7 行元数据)
- "我会默认遵守 [一长串自己组装的规则]"(等于宣告自己没读全就开口)

## 多人 + 多版本:项目记忆放在哪、候选写到哪

skill 把"安全编辑"做完了,但**经验沉淀 + 团队同步**还有一层独立于 VCS 的设计:谁产出的项目记忆,放到哪个目录,下个会话/同事的 AI 怎么读到。这一层 skill 自己**不绑定具体 VCS**,只规定文件系统上的稳定落点;同步走 git / svn / 共享盘 / 邮件包都行,团队自己定。

### 三层知识架构

```
Layer 1  通用工作流 / 反模式 / 模板        skill 仓 ~/.codex/skills/.../
Layer 2  本项目特有约定 (跨版本共享)        工程仓 <project>/.ai-config-table/
Layer 3  个人本地笔记 (可选)                .ai-config-table.local/(.gitignore)
```

读取顺序 Layer 1 → 2 → 3,后者补充前者。**skill 只负责沉淀(写文件)**,同步机制(git push/pull、svn ci/up、Dropbox/坚果云、共享盘、邮件包)是团队的事。

### Layer 2 落点判断 —— VCS 无关

| ✓ 该放 | ✗ 不该放 |
|---|---|
| 工程元数据所在的仓(`.codex/` / `AGENTS.md` / `.cursorrules` / `CLAUDE.md` / `src/` 同级) | 配置源表镜像 / SVN 自动同步目录(下次同步会覆盖) |
| 团队主开发仓(进 VCS 就能共享) | 客户端 build 产物目录 |
| 用户明确愿意 commit 给团队的仓 | 临时挂载的共享盘内容(挂载断开就丢) |
| Dropbox / 坚果云 / OneDrive 等**双向同步盘**(同步不覆盖,默认可放) | 如果用户明示"别在镜像目录乱写文件"→ **听用户**,挪到普通工程仓 |
| 单仓 SVN 工作副本(`.svn/` 同级,允许 `svn add`) | 单仓 SVN 的 build/output/auto-generated 子目录 |

判断方法:**问自己"这个目录会被某个**单向**自动化机制覆盖吗?"** 会就别放,不会才放(双向同步不算覆盖)。**用户明示偏好永远盖过通用判断**。

### 「工程仓」(`<工程仓>`)在文件系统上怎么找

`<工程仓>` 不是某个固定路径,**是 AI 需要识别的概念**。按下面 4 级优先级:

1. **用户明示**:用户说"项目根在 `~/work/proj/`"或直接传 `--memory-root` —— 这条最强。
2. **profile.md 里写明**(已有项目):`<工程仓>/.ai-config-table/profile.md` 里如果有 `engineering_repo: <path>` 字段,按这个走。
3. **从 `<root>` 向上找 marker 文件**,取第一个命中的目录:
   - `.codex/` / `AGENTS.md` / `CLAUDE.md` / `.cursorrules`(agent 元数据)
   - `.git/` / `.svn/`(VCS 标记)
   - `package.json` / `Cargo.toml` / 项目自有的总入口
4. **都没找到** → 把 `<root>` 当工程仓(单仓项目的退化情况)。

### inspect 向上回溯(已实现)

`inspect --root <配置目录>` 启动时,从 `<root>` 沿 parent **最多回溯 3 层**找 `.ai-config-table/`,找到的第一个作为 Layer 2 渲染 Project Memory。这覆盖**单仓 + 子目录配置**的最常见形态(配置在 `<工程仓>/data/configs/` 之类的位置,记忆在 `<工程仓>/.ai-config-table/`)。

stderr 会打印实际找到的路径:`[inspect] project memory found N parent(s) above --root: <path>`,**有这一行就说明继承成功**。

3 层内都没找到 → 走 *不熟悉的库* 流程,任务尾部问用户"是否要在 `<工程仓>/.ai-config-table/` 入档"。**绝不在镜像目录或来源不明的 `<root>` 自己原地建 `.ai-config-table/`**。

### 跨仓拓扑:配置源在 SVN、工程仓在 git(GameDevelop 形态)

当配置事实源**不在工程仓的目录树**内(例:配置 `/Users/Shared/configs-svn/develop/`,工程仓 `~/work/proj/`),parent 回溯永远跨不过两棵独立目录树 —— 这时显式传 `--memory-root <工程仓>`:

```bash
python3 scripts/inspect_config_tables.py \
  --root /Users/Shared/configs-svn/develop \
  --memory-root ~/work/proj \
  --output /tmp/inventory.md --format md
```

`learn.py` 同理:写入时也支持 `--memory-root`,确保读写落同一个目录,**A 入档 B 能读到**。

每次跨仓 inspect 都加 `--memory-root` 烦人 → 把 `engineering_repo` 写到 `profile.md`(下一节),AI 第一次接入时读到,后续自动用它。

### `profile.md` 最小 schema

`<工程仓>/.ai-config-table/profile.md` 是 AI 跟用户共编的"项目身份证":7 字段(`engineering_repo` / `config_root` / `external_config_root` / `baseline` / `current_version` / `known_versions` / 写表入口),inspect 把它整段 dump 进 Project Memory 段,后入 AI 肉眼读。

**完整 schema 模板、字段说明、触发更新时机 → [`references/profile-schema.md`](references/profile-schema.md)**。跨仓拓扑要填 `external_config_root`;多版本项目要填"多版本布局"段。

### 多版本配置管理(项目有 trunk + version_*/ 这种布局时)

游戏团队常见布局:

```
<配置仓>/
├─ trunk/           ★ 线上源(改动最终回归这里;diff 的基准)
├─ version_1.0/     已上线版本(等回归 trunk)
├─ version_1.1/     开发中版本
└─ version_1.2/     规划中版本

<工程仓>/.ai-config-table/   ★ 项目记忆放这里,跨版本共享
```

skill 在这种项目里 6 条铁律:

1. **第一次接入主动问 + 落档**:哪个目录是线上源、当前任务针对哪个版本,**两个分别问**,任一缺失继续问。落到 `<工程仓>/.ai-config-table/profile.md` 的"多版本布局"段,以后不再问。**不要靠猜 `trunk` / `main` / `live` 命名**,问用户最稳。话术样例:

   > 看到你这项目有 `trunk` 和几个 `version_*/` 目录。动手前两件事:
   > - **线上源**(改动最终回归这里、diff 的对照基准)是哪个?
   > - 这次任务针对的是**哪个版本目录**?
   > 答完我记到 profile.md,以后不再问。

2. **候选回填永远同版本目录、同子路径**:改 `version_1.1/data/Skill.xlsx`,候选写到 `version_1.1/data/Skill_candidate.xlsx`(同目录,不是同版本根),**不跨版本**。绝不主动把改动写到 trunk 或别的版本目录。

3. **`--root` 传当前版本目录,不是 `<配置仓>` 根**:`inspect --root <配置仓>/version_1.1/` —— 这样 inspect 只扫当前版本,不会把 4 个版本同名表混在一起。Project Memory 会通过向上回溯找到 `<工程仓>/.ai-config-table/`。

4. **跨版本 merge / 回流是 VCS 的活,不是 skill 的活**:用户说"把 v1.1 改动同步到 trunk",AI 走两步:
   - (a) **批量列 diff(只读,允许)**:遍历 v1.1 下涉及的表,挨个 `diff_config_tables.py --source trunk/X --candidate version_1.1/X --output diffs/X.md`,汇总成一份清单交给用户
   - (b) **拒绝自动 merge / cherry-pick / 覆盖 trunk**:让用户走他们自己的 git/svn 工具按清单同步
   - 边界:**只读列 diff = 允许**,**任何写 trunk 的动作 = 拒绝**。

5. **项目记忆默认项目级**:`<工程仓>/.ai-config-table/` 跨版本共享(col2 备注列、行号引用这种是整项目成立)。极少数版本特有规则才下沉到版本目录的 `.ai-config-table/`;**inspect 第一版只读找到的第一个,不做叠加**。如果你判断某条规则真的只在某版本成立,问用户落到哪一层。

6. **改 trunk 高危**:trunk = 线上,用户没明示"改 trunk"前,**默认假设当前任务在某个 version_*/ 而不是 trunk**。如果用户没说,主动问一次。

### 反例 —— 看到自己写下面这种立刻停

- 用户说"改 X 表",AI 不问版本直接改了 `trunk/`(★ trunk = 线上,高危)
- 用户说"改 v1.1 的 X",AI 把候选写到 `trunk/` 或别的版本目录
- 用户说"同步到 trunk",AI 直接跨版本自动 merge(应该走 VCS,skill 只列 diff)
- 把 `.ai-config-table/` 写在 SVN 自动同步镜像里(下次 svn up 覆盖掉)
- 用户没明示哪个是线上源,AI 自己猜了 `trunk` / `main` / `live` 名字
- 默认 VCS 是 git,看到 svn 工作副本就建议"先 git init"(★ 不要绑 VCS)

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

## 对话样例

下面 5 段示范 *对话的形状*,具体措辞按用户语气调整。

### 样例 1 — 用户给一个文件夹路径

> **用户**: 帮我看下我配置表里 Item 表的 10001 是什么
>
> **AI**: 好,你的配置表在哪儿?给我一个文件夹路径,或者直接把 Excel 文件拖给我。
>
> **用户**: `~/myproj/cfg/`
>
> **AI**: *(后台跑 inspect,自己读结果)* 找到了。`Item.xlsx` 前 4 行是表头(中文名 / 英文字段 / 类型 / 备注),数据从第 5 行开始。10001 这一行是:Sword(剑),描述 "A basic sword.",图标 `icon_sword`,品质 1。要改什么?

### 样例 2 — 用户想改一个值

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

### 样例 3 — 用户加新行(跨表引用风险)

> **用户**: 帮我加 5 个新道具进 Item 表,ID 从 10020 开始
>
> **AI**: 没问题。这种加新道具的事,通常配套要做的事不少 —— 文本表里的中文名、图标资源表里的对应条目,如果只加 Item 不加这些,游戏里可能显示空白。在你给我中文名图标之前,我先把工作分两部分:
>
> - **你来定**:5 个道具的中文名、描述、图标资源名 / 路径
> - **我来核**:ID 10020-10024 这段没被占用、文本表(LocText 这种)和图标表的格式
>
> 你把中文名图标发我,我扫完就告诉你后续要不要补哪几张表。

### 样例 4 — 用户不知道结构怎么回答

> **用户**: 不知道,你看着办
>
> **AI**: OK 我先看一眼,5 秒。*(跑 inspect)* 看完了。Item 表第 1 行是中文(物品ID / 名称 / 描述 …),第 2 行是英文字段名(ItemID / Name / Desc …),第 3 行是类型,数据从第 5 行开始 —— 这种 4 行表头很常见,我按这个理解处理。唯一 ID 是 `ItemID`,我用它定位行。继续?

### 样例 5 — 用户想跳步骤

> **用户**: 直接帮我把改完的文件覆盖回去就行,别给我看什么副本了,麻烦
>
> **AI**: 副本和 diff 是这工具的底线 —— 没有它们我一旦改错没法救,所以这两步省不掉,但**我可以把它们压成一句话**:我生成 `X_candidate.xlsx`,然后用一句话告诉你改了哪几格。你看着对就一个字 OK,我再覆盖回原文件;不对你说哪不对,我改 patch 重来。**覆盖前必须你点头**。这样既不绕路,也不会把你原文件改坏。

### 样例 6 — 用户说不清哪张表(用 find_table)

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

### 样例 7 — 字段不懂含义(5 个证据来源 + 带证据问)

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

### Dialogue (English flavor)

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

## 副本里我们保留什么、可能丢什么

这个 skill 用 `openpyxl` 读写 `.xlsx`。**重要**:底层可以读写公式文本,但配表改动流程默认把"源表含公式"当成需要确认的风险,必须先确认处理方式(转值 / 无公式导出 / 沿用公式)再 patch。

在源表已无公式的前提下,**一般会保留**:

- 单元格的值、文本
- 基础样式(字体 / 字号 / 颜色 / 边框 / 数字格式)
- 合并单元格、批注
- 列宽、行高、命名区域
- `.xlsm` 文件的 VBA(脚本)

**可能改掉或丢失**(`diff_config_tables.py` 不比较这些,看不出来):

- 数据验证下拉框(尤其长枚举或跨表引用)
- 复杂条件格式(Excel 里手写的复杂规则)
- 嵌入图表(老版 Excel 创建的)
- 打印设置、自定义视图

如果用户的工作簿依赖任何「可能丢」的东西 —— **主动告诉用户**:生成副本之后,**让他先用 Excel / WPS 打开候选肉眼对比一次**再决定要不要覆盖。

## Windows + 非 ASCII 路径(中文目录名)—— 用 `--config` 模式

Windows 默认代码页是 cp936/GBK,不是 UTF-8。当你 spawn 子进程把中文路径作为命令行参数传给 Python 时,中间这一层经常会把中文字静默替换成 `?`,Python 收到的就是坏路径(`C:\TR\????\??\X.xlsx`),开文件会报 `OSError: [Errno 22] Invalid argument`。这是 Windows + 非 ASCII argv 的经典坑,Python 里面没法挽回。

**正确做法:用 `--config FILE` 模式,把所有参数(包括路径)写在 UTF-8 JSON 文件里,绕开 argv 编码**。

四个脚本(inspect / patch_xlsx / diff / validate_refs)都支持 `--config`。**规则**:

1. 在一个**纯 ASCII 路径**(如 `C:\Temp\`、skill 自身目录、系统 temp 目录)下写一个 UTF-8 JSON,key 用 argparse 的 dest 名(下划线、不带 `--`):

   ```json
   {
     "root": "C:\\TR\\配置表\\装备",
     "field_row": 2,
     "meta_rows": [1, 3, 4],
     "output": "C:\\TR\\配置表\\装备\\inventory.md",
     "patch_template": "C:\\Temp\\patch.json",
     "format": "md"
   }
   ```

2. 用纯 ASCII 路径调用脚本,其他参数全在 JSON 里:

   ```bash
   python3 scripts/inspect_config_tables.py --config C:\Temp\inspect_config.json
   ```

3. patch_xlsx / diff / validate_refs 同理。

**何时切到 --config 模式**:
- 用户的配置路径里含中文、日文、韩文等任何非 ASCII 字符
- 你在 Windows 上,不确定终端是 cp936 还是 UTF-8
- 脚本报 `路径里检测到 '?' 字符` 错误时

脚本会**自动检测路径里有 `?` 字符**(典型的 cp936 替换痕迹),直接报清晰错误告诉你切到 `--config`。

Mac / Linux 默认 UTF-8,中文路径直接走 argv 也没问题,不强制用 `--config` 模式 —— 但用了也行,完全等价。

## 沙盒不让你覆盖原表怎么办 —— 别绕,交给用户

很多运行环境(Codex 沙盒、Claude Code 限制模式、Cursor)会拒绝**覆盖用户原文件**,即使用户说要覆盖。这是正常的保护。**绝对不要**:

- `sudo` / 提权 / `--dangerously-*` 任何形式的绕过
- 写到旁路再 `mv` 回去
- 让用户去关安全开关

**正确动作**:把副本路径告诉用户,给他 3 步手动操作:

> 我已经把改好的版本生成到这里:
>
> `~/myproj/cfg/Item_candidate.xlsx`
>
> 不过我这边不允许直接覆盖你的原文件 `Item.xlsx`,这是默认的安全保护。请你手动:
>
> 1. 关掉 Excel(如果它正开着原文件)
> 2. 把 `Item.xlsx` 改名为 `Item_backup.xlsx`(保险)
> 3. 把 `Item_candidate.xlsx` 改名为 `Item.xlsx`
>
> 三步,30 秒。**如果你原文件名很长 / 带版本号**(比如 `Item_v3_final_用这个.xlsx`),直接告诉我准确的文件名,我把这两条改名指令写完整给你。

副本就是交付物,最后那一步用户自己关闭闭环 —— 这是用户的安全网,不是要绕过的障碍。

## 用户给的信息模糊怎么办

非常常见。两类:**说不清哪张表** 和 **字段不懂含义**。两个都不许直接猜,也不要直接抛回去问"哪张表?" / "这字段啥意思?" —— 用户嫌烦,你显得没用。

**统一原则:先用你手里的数据找证据,带着证据再问**。

### A. 用户说不清哪张表(例:"去世界 boss"、"那张冒险表"、"商店那个")

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

### B. 字段不懂含义(例:"ConditionExtra"、"Coefficient"、"AssetCode")

5 个证据来源,**挨个查再问**:

| 证据 | 怎么用 |
|---|---|
| **inspect sample** | 拉 3-5 行实际值。`1,1` / `0,0`?百分数?ResId 引用?值就在暗示含义 |
| **meta_rows(注释行)** | 多行表头里通常有一行写策划注释。`field_row=2 meta_rows=[1,3,4]` 的 4 就是 |
| **跨 sheet 同名字段** | 这个字段在其他 sheet 是不是也出现过?那张表的样本 / 注释清不清楚 |
| **`.ai-config-table/learned-patterns.md`** | 项目记忆里有没有人记过这个字段 |
| **RPG 反模式 1**(`references/rpg-config-patterns.md`) | 是不是 ID 段字段?有没有独立业务字段才是真相 |

**带证据问** —— 不要空问"这字段啥意思":

> `ConditionExtra` 我看了 5 行样本,值都是 `1,1` / `0,0` 这种两位整数对。第 4 行备注写"触发参数"。看着像 `(参数1, 参数2)` 格式,但具体含义没明确文档。
>
> 你能确认:
> - 这是 (参数1, 参数2) 还是单值?
> - 1 和 0 分别什么意思?
> - 我这次要配的新条目,应该填什么?

具体、有锚点、可直接答 —— 比"这个字段啥意思?"好用 10 倍。

### 学到了就入档

用户答了之后,**主动问"要不要存档?"**。用户说存就跑 `scripts/learn.py`(参见下面"项目记忆"),下次同项目不再问。

---

## 项目记忆 (.ai-config-table/) —— 入档操作手册

**这一节只讲"怎么入档、什么时候入档、入档话术"**。落点规则 / 上溯逻辑 / 多版本布局 / 跨仓拓扑 / VCS 同步机制 / 跨人时序 —— 全部见前面 *[多人 + 多版本:项目记忆放在哪、候选写到哪](#多人--多版本项目记忆放在哪候选写到哪)* 章节 + 它链出去的 `references/profile-schema.md` / `references/sync-mechanisms.md`。

**铁律:任何累积都是用户明示同意后写入,绝不静默积累**。

### 入档的起点:inspect 的 "配表规律候选"

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

### 什么时候建议入档

任务跑完后,**主动问用户**(用户说"存"才存)。值得入档的信号:

- 稳定的 **命名规律**(LocKey 都是 `ITEM_<id>_NAME`、技能 ID 第 3 位代表槽位)
- 摸清的 **跨表引用约定**(Reward.ItemID → Item.ItemID、Skill.BuffID#N → Buff.BuffID)
- 用户**否决**过的判断(他说 X 不能这样改,要存下来下次别再问)
- **特殊字段** 含义(`AssetCode` 实际不是资源 id 而是分包代码,这种)

### 入档话术

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

### 怎么入档 —— `learn.py` 一条命令

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
- 找不到 → 在 `<root>/.ai-config-table/` 新建 + 写 README + 初始化 `learned-patterns.md`
- 跨仓拓扑 → 加 `--memory-root <工程仓>` 强制锁定
- stderr 打印实际落到哪个目录,对账方便

**`topic` 用稳定 slug**(英文小写 + 短横线),原因见 [`references/sync-mechanisms.md`](references/sync-mechanisms.md#跨人入档时序约定)。

### profile.md (跟 `learned-patterns.md` 平行的另一份记忆)

`profile.md` 装项目级长期约定(路径锚点 / 多版本布局 / 写表入口)。**没专门脚本**,AI 用 Read / Write 直接维护;inspect 自动把它整段塞进 Project Memory 段。

Schema + 字段说明 + 触发更新时机 → [`references/profile-schema.md`](references/profile-schema.md)。

---

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
6. **按任务大小做差集**,拿到确认。**差集详细程度跟任务复杂度匹配,见下面 "差集详细程度按任务大小分级"**。复述时主动应用 `references/rpg-config-patterns.md` 里的 5 条心智模型。
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
   如果本轮沿用公式,候选用 Excel / WPS 或项目工具重算并保存后,加公式结果校验:
   ```bash
   python3 scripts/diff_config_tables.py --source X.xlsx --candidate X_candidate.xlsx --output diff.md --compare-formula-results
   ```
   `missing_formula_results` 必须为 0;`formula_result_changes` 必须和用户确认过的最终结果一致。
10. **validate_refs 跨表对账**(默认 per-sheet auto-detect,不用传参):
   ```bash
   python3 scripts/validate_refs.py --workbook X_candidate.xlsx
   ```
   **exit 非 0 = 有 orphan,先解决再覆盖**。
11. **把副本路径告诉用户**,等明确"覆盖"指令。**沙盒拒写就不绕**,把路径交给用户手动操作(参见上面 *沙盒不让你覆盖原表怎么办*)。
12. **任务结束前**,如果过程中发现了稳定的项目规律(命名约定 / 跨表对应 / 否决过的做法 等),**主动问用户**"要存到 `.ai-config-table/` 吗?",用户说存就跑 `scripts/learn.py`。下次开工就少问一遍。

**任何一步报错,先读错误信息**:脚本现在会给出"Did you mean …?" 的建议(field / sheet / key 拼错时),`?` 路径会提示用 `--config`,Excel 锁文件会提示关闭工作簿。**不要尝试绕过错误,按错误信息修**。

## RPG 配表通用心智模型(复述改动前心里过一遍)

跟用户复述改动前,**心里过一遍** `references/rpg-config-patterns.md` 里 5 条通用 RPG 配表反模式 / 方法。具体到当前任务,只在该条适用时主动提:

1. **不要从 ID 段推业务语义** —— 用户说"按 ID 段过滤 X 类型"时,跟他说"我用 Type 字段过滤更稳"
2. **业务分类查 Desc 不查 I18N** —— 用户说"按中文名找内部分类标签",提醒标签在 Desc / Type 字段
3. **摸底必扫系统下所有 sheet 字段** —— 用户问"X 系统有没有 Y 字段",别看 sheet 名,grep 所有 sheet 列头
4. **配新表前先盲配 3-5 条已有的对答案** —— 用户要"参照 N 条配 M 条",自己先盲建 3-5 条对比
5. **表结构决策原则** —— 用户要新建表 / 加字段,先回答 3 个决策问题(扩展? ID 引用? 旧字段兼容?)

**每个项目的字段命名 / 表结构 / 命名约定不同** —— 这 5 条只给"思考方向",不是标准答案。具体项目用 `references/project-profile-template.md` 建档,覆盖默认假设。

## 按任务复杂度走不同流程

简单任务别上完整流程,**差集详细程度也跟着任务大小走** —— 不要 1 格改也搞 4 段汇报。

| 任务 | 跑哪几步 | 差集格式 |
|---|---|---|
| 查某个字段是啥 | inspect → 回答 | 不用差集 |
| 改一行某个值,无跨表 | inspect → 1 句话总结 → dry-run → 用户 OK → 生成 → diff | **1 句话**:"改 X 行 Y 字段 Z→W,其他不动" |
| 加 1-5 行 | inspect → **4 段差集** → dry-run → 生成 → diff → validate_refs | **4 段差集**(见下) |
| 源表有公式 | inspect / patch 报公式 → 先问用户处理方式;转值 / 无公式导出后重新 inspect,沿用公式则走带公式流程 | 先不生成差集,解除阻塞后再按原任务分级 |
| 10+ 行 / 新 ID / 跨表 / 表结构 | 完整流程 + spec | **4 段差集 + spec 兜底** |

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

完整 spec 用 `references/change-spec-template.md` 模板(AI 内部走清单,给用户看一段话总结)。4 段差集仍然要做,spec 是兜底用的内部文档。

**关键**:**4 段差集只用在"加 1-5 行"以上的任务**。改一格不要搞 4 段,显得啰嗦。

## 完整流程(中 / 高风险任务)

### 1. 发现

```bash
python3 scripts/inspect_config_tables.py --root /path/to/config --format md --output /path/to/config/inventory.md
# 多行表头:
python3 scripts/inspect_config_tables.py --root /path/to/config --field-row 2 --meta-rows 1,3
# 跳过样例 patch:
python3 scripts/inspect_config_tables.py --root /path/to/config --ignore '*-patch.json'
# 同时生成一份 patch JSON 骨架(下一步直接在骨架上填,不用凭印象写):
python3 scripts/inspect_config_tables.py --root /path/to/config --patch-template /path/to/config/patch.json
```

> 上面例子里 root 是目录;如果 root 是**单个文件**(`/path/to/sample.xlsx`),把 `--output` / `--patch-template` 改写到**该文件的父目录**(`/path/to/`),不要拼成 `/path/to/sample.xlsx/inventory.md` —— 那是非法路径。详见 [`references/unknown-project-onboarding.md`](references/unknown-project-onboarding.md) 第 2 步。

inspect 现在会自动建议:**如果第 1 行像中文显示名、第 2 行像英文字段名,会提示 `--field-row 2 --meta-rows 1`**。看到 hint 跟用户确认一下再走。

**`--patch-template` 强烈推荐**:它会为每张 Excel sheet 预填 `field_row` / `meta_rows` / `data_start_row` / `key_field` 和 `_fields_available` 字段名列表。你只需要在 `updates` / `appends` 数组里加内容就行,**不要凭印象写 patch JSON 的 schema**。

### 2. 公式闸门

如果 inventory 里出现 `FORMULA WARNING`,先停下。告诉用户公式位置示例,让用户选择:清公式 / 粘贴为值、导出无公式版本,或沿用公式。

`patch_xlsx.py` 也会在 dry-run 和实际 patch 前检查源工作簿;只要还有公式就直接拒绝继续。

如果用户明确说公式要沿用 / 保留,按上方"带公式流程"处理,不要把 `--allow-formulas` 当普通开关。

### 3. 建项目档案(可选)

复杂项目首次接入时,**AI 内部** 用 `references/project-profile-template.md` 走一遍流程,留底自己用。**不要丢给用户填**。

反复做同一个项目,按 `references/config-reference-playbook.md` 搭知识层。

### 4. 跟用户确认

用大白话:动哪个文件、加 / 改 / 删哪几行、可能影响哪些别的表、只生成副本还是会覆盖、风险高低。

### 5. (中 / 高风险)用 spec 自我组织

**AI 内部** 用 `references/change-spec-template.md` 整理思路 —— 给用户看一段话总结,完整 spec 自己留底,不要落盘给用户。

### 6. 生成副本

**patch JSON 的精确格式见 [`references/patch-format.md`](references/patch-format.md)**(不要凭印象写 — 用 inspect 的 `--patch-template` 拿骨架,在骨架上填)。

```bash
python3 scripts/patch_xlsx.py --source table.xlsx --output table_candidate.xlsx --patch changes.json --dry-run
python3 scripts/patch_xlsx.py --source table.xlsx --output table_candidate.xlsx --patch changes.json
```

`--source` 和 `--output` **必须是不同的文件**,脚本不会原地编辑 — 一开始就会报错。

如果 `--output` 已存在,默认会自动加时间戳(`table_candidate_20260512_103045.xlsx`),不会报错。要强制覆盖加 `--force`,要严格报错加 `--strict`。

如果 `--output` 所在目录写不进去(沙盒限制),脚本会**自动 fallback 写到 `~/Downloads/<同名>`**,并在 stderr + 输出 JSON 里告诉你实际路径。把这个路径告诉用户即可。

### `note` 字段(备注列)

每个 update **可以加 `note`**(一句话说明改动原因)。如果表里有列叫 `备注` / `Note` / `Comment` 之类,patch_xlsx 会把这段文本写到这一行的备注列里 —— 直接形成审计痕迹。

```json
{"key": "10003", "field": "Quality", "value": 3, "note": "品质 2 -> 3, 平衡性调整"}
```

**推荐**:每个改动都顺手填一句 `note`。表里看就知道这格谁改的、为什么。Appends 想填备注直接在 row 字典里写 `"备注": "..."`。

### 7. 校验

```bash
python3 scripts/diff_config_tables.py --source table.xlsx --candidate table_candidate.xlsx --output diff.md
# 沿用公式时,先用 Excel / WPS 或项目工具重算候选并保存,再加:
python3 scripts/diff_config_tables.py --source table.xlsx --candidate table_candidate.xlsx --output diff.md --compare-formula-results
# 跨表引用对账:
python3 scripts/validate_refs.py --workbook table_candidate.xlsx --field-row 2 --meta-rows 1,3,4
```

带公式流程里,`missing_formula_results` 非 0 = 候选还没有可读的公式计算结果,不能覆盖。`formula_result_changes` 不是自动失败,但必须逐项对照"最终要的结果"确认。

`validate_refs.py` 自动检测「`Item.LocKey` 指向 `LocText.LocKey`」这种引用,跑出来如果有 orphan,**先解决再覆盖**。

`references/validation-checklist.md` 是 **AI 内部** 走清单用 —— 给用户一段话总结就行。

### 8. 交付

- 副本绝对路径
- 一段话:改了什么
- 需要用户决定的事
- 能不能帮他覆盖,还是他自己拷(参见 *沙盒不让你覆盖原表怎么办*)

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
- **后入 AI 继承不审计**。`.ai-config-table/` / inventory / 项目本地 README / 表字段索引 已存在 → 先读再说话,不要在第一轮发"硬问题清单"或自组规则(见 *你不是第一个 AI 时 —— 后入者守则*)。
- **沉淀 ≠ 同步**。skill 只管把项目记忆写到 `.ai-config-table/`;同步走 git / svn / 共享盘 / 邮件包 由团队定,**skill 不绑 VCS**(见 *多人 + 多版本* 章节)。
- **多版本项目先问版本**。看到 `trunk/` + `version_*/` 这种布局,先问"线上源是哪个 / 当前任务针对哪个版本",落到 `profile.md`,以后不再问;**没明示前不动 trunk**。
- **多行表头是常态**(中文名 / 英文字段 / 类型 / 注释)。inspect 会主动建议。
- **编码降级**:CSV / JSON 默认 UTF-8 解码失败自动尝试 GBK。
- **沙盒拒写 = 用户安全网**,不是要绕的障碍。

## 与 agent runtime 兼容

纯 Python + Markdown,无 MCP / 插件 / SaaS。Python 3.8+ 即可。

- **Codex CLI**: `git clone https://github.com/1aita0v/ai-config-table-skill.git "${CODEX_HOME:-$HOME/.codex}/skills/ai-config-table"`
- **Claude Code(用户级)**: `git clone https://github.com/1aita0v/ai-config-table-skill.git ~/.claude/skills/ai-config-table`
- **Claude Code(项目级)**: `git clone https://github.com/1aita0v/ai-config-table-skill.git .claude/skills/ai-config-table`
- **Cursor / Aider / 其他**: 文件夹丢到 agent 看得见的地方,在 `.cursorrules` / `AGENTS.md` / `CLAUDE.md` 加一行指向 `ai-config-table-skill/SKILL.md`。

依赖:Python 3.8+。`.xlsx` / `.xlsm` 还需要 `openpyxl`。建议 `pip install -r requirements.txt`(把版本钉在测过的范围),急用直接 `pip install openpyxl` 也行。CSV / TSV / JSON 用标准库。inspect 和 patch 的 JSON 输出都带 `tool_versions` 字段,issue 复现更可靠。

## 文件结构

- `scripts/` —— `inspect_config_tables.py`(扫描)、`patch_xlsx.py`(生成副本)、`diff_config_tables.py`(对比)、`validate_refs.py`(跨表引用对账)。
- `references/` —— AI 看的参考:
  - `rpg-config-patterns.md` —— **通用 RPG 配表 5 条反模式 / 方法**(复述改动前心里过一遍)
  - `patch-format.md` —— `patch_xlsx.py` 接受的 JSON 格式(含 `note` 字段)
  - `data-sources.md` —— 数据源选择路由
  - `no-data-source-report.md` —— 找不到数据源时的失败模板
  - 以下 3 个是 **AI 内部** 走流程用,**不要丢给用户填表**:
    `project-profile-template.md`、`change-spec-template.md`、`validation-checklist.md`、`config-reference-playbook.md`
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

**多人 / 多版本 / 跨仓特有反模式**(完整清单见 *[后入者守则反例](#反例--看到自己写下面这种立刻停)* 和 *[多版本反例](#反例--看到自己写下面这种立刻停-1)* 两节):
- 后入 AI 把项目本地约定 / 旧工具引用 / 包结构当成 skill bug 来 audit
- 多版本项目里不问版本就改 `trunk/`(★ trunk = 线上,高危)
- 跨版本 merge / 回流让 AI 自动做,而不是让用户走 VCS
- 把 `.ai-config-table/` 写在 SVN 自动同步镜像里(下次同步会丢)
- 默认 VCS 是 git,看到 svn / Dropbox 就建议改 git(★ skill 不绑 VCS)
