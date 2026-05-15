# 多人 + 多版本 + 跨仓 —— 项目记忆放哪、候选写哪

主 SKILL.md 简单 case 直通车里有钩子:看到 `trunk/` + `version_*/` 布局、跨仓拓扑、需要团队同步项目记忆时,打开本文件。

skill 把"安全编辑"做完了,但 **经验沉淀 + 团队同步** 还有一层独立于 VCS 的设计:谁产出的项目记忆,放到哪个目录,下个会话/同事的 AI 怎么读到。这一层 skill 自己 **不绑定具体 VCS**,只规定文件系统上的稳定落点;同步走 git / svn / 共享盘 / 邮件包都行,团队自己定。

## Contents

- [三层知识架构](#三层知识架构)
- [Layer 2 落点判断 —— VCS 无关](#layer-2-落点判断--vcs-无关)
- [「工程仓」在文件系统上怎么找](#工程仓在文件系统上怎么找)
- [inspect 向上回溯(已实现)](#inspect-向上回溯已实现)
- [跨仓拓扑:配置源在 SVN、工程仓在 git(GameDevelop 形态)](#跨仓拓扑配置源在-svn工程仓在-git-gamedevelop-形态)
- [`profile.md` 最小 schema](#profilemd-最小-schema)
- [正式环境识别 / 脏数据警示](#正式环境识别--脏数据警示)
- [多版本配置管理(trunk + version_*/)](#多版本配置管理项目有-trunk--version_-这种布局时)
- [另一种主流方案:分支独立仓 + CI 合并流水线](#另一种主流方案分支独立仓--ci-合并流水线)
- [反例 —— 看到自己写下面这种立刻停](#反例--看到自己写下面这种立刻停)

## 三层知识架构

```
Layer 1  通用工作流 / 反模式 / 模板        skill 仓 ~/.codex/skills/.../
Layer 2  本项目特有约定 (跨版本共享)        工程仓 <project>/.ai-config-table/
Layer 3  个人本地笔记 (可选)                .ai-config-table.local/(.gitignore)
```

读取顺序 Layer 1 → 2 → 3,后者补充前者。**skill 只负责沉淀(写文件)**,同步机制(git push/pull、svn ci/up、Dropbox/坚果云、共享盘、邮件包)是团队的事。

## Layer 2 落点判断 —— VCS 无关

| ✓ 该放 | ✗ 不该放 |
|---|---|
| 工程元数据所在的仓(`.codex/` / `AGENTS.md` / `.cursorrules` / `CLAUDE.md` / `src/` 同级) | 配置源表镜像 / SVN 自动同步目录(下次同步会覆盖) |
| 团队主开发仓(进 VCS 就能共享) | 客户端 build 产物目录 |
| 用户明确愿意 commit 给团队的仓 | 临时挂载的共享盘内容(挂载断开就丢) |
| Dropbox / 坚果云 / OneDrive 等 **双向同步盘**(同步不覆盖,默认可放) | 如果用户明示"别在镜像目录乱写文件"→ **听用户**,挪到普通工程仓 |
| 单仓 SVN 工作副本(`.svn/` 同级,允许 `svn add`) | 单仓 SVN 的 build/output/auto-generated 子目录 |

判断方法:**问自己"这个目录会被某个 单向 自动化机制覆盖吗?"** 会就别放,不会才放(双向同步不算覆盖)。**用户明示偏好永远盖过通用判断**。

## 「工程仓」在文件系统上怎么找

`<工程仓>` 不是某个固定路径,**是 AI 需要识别的概念**。按下面 4 级优先级:

1. **用户明示**:用户说"项目根在 `~/work/proj/`"或直接传 `--memory-root` —— 这条最强。
2. **profile.md 里写明**(已有项目):`<工程仓>/.ai-config-table/profile.md` 里如果有 `engineering_repo: <path>` 字段,按这个走。
3. **从 `<root>` 向上找 marker 文件**,取第一个命中的目录:
   - `.codex/` / `AGENTS.md` / `CLAUDE.md` / `.cursorrules`(agent 元数据)
   - `.git/` / `.svn/`(VCS 标记)
   - `package.json` / `Cargo.toml` / 项目自有的总入口
4. **都没找到** → 把 `<root>` 当工程仓(单仓项目的退化情况)。

## inspect 向上回溯(已实现)

`inspect --root <配置目录>` 启动时,从 `<root>` 沿 parent **最多回溯 3 层** 找 `.ai-config-table/`,找到的第一个作为 Layer 2 渲染 Project Memory。这覆盖 **单仓 + 子目录配置** 的最常见形态(配置在 `<工程仓>/data/configs/` 之类的位置,记忆在 `<工程仓>/.ai-config-table/`)。

stderr 会打印实际找到的路径:`[inspect] project memory found N parent(s) above --root: <path>`,**有这一行就说明继承成功**。

3 层内都没找到 → 走 *不熟悉的库* 流程,任务尾部问用户"是否要在 `<工程仓>/.ai-config-table/` 入档"。**绝不在镜像目录或来源不明的 `<root>` 自己原地建 `.ai-config-table/`**。

## 跨仓拓扑:配置源在 SVN、工程仓在 git(GameDevelop 形态)

当配置事实源 **不在工程仓的目录树** 内(例:配置 `/Users/Shared/configs-svn/develop/`,工程仓 `~/work/proj/`),parent 回溯永远跨不过两棵独立目录树 —— 这时显式传 `--memory-root <工程仓>`:

```bash
python3 scripts/inspect_config_tables.py \
  --root /Users/Shared/configs-svn/develop \
  --memory-root ~/work/proj \
  --output /tmp/inventory.md --format md
```

`learn.py` 同理:写入时也支持 `--memory-root`,确保读写落同一个目录,**A 入档 B 能读到**。

每次跨仓 inspect 都加 `--memory-root` 烦人 → 把 `engineering_repo` 写到 `profile.md`(下一节),AI 第一次接入时读到,后续自动用它。

## `profile.md` 最小 schema

`<工程仓>/.ai-config-table/profile.md` 是 AI 跟用户共编的"项目身份证":7 字段(`engineering_repo` / `config_root` / `external_config_root` / `baseline` / `current_version` / `known_versions` / 写表入口),inspect 把它整段 dump 进 Project Memory 段,后入 AI 肉眼读。

**完整 schema 模板、字段说明、触发更新时机 → [`profile-schema.md`](profile-schema.md)**。跨仓拓扑要填 `external_config_root`;多版本项目要填"多版本布局"段。

## 正式环境识别 / 脏数据警示

**不仅仅是 `trunk + version_*/` 这种规范多版本** —— 多数项目还有更杂的形态:`new/` 并行重写、`backup/` 历史快照、`dev/` 开发、`test/` 验证、`temp/` 实验沙盒、`v1/` `v2/` 历史归档…… 这些目录里都是 **真实可读的配置数据**,但 **只有一份是当前线上 / 正式环境**,其他全是脏数据。

inspect 的 *配表规律候选 → cat 8 目录层级* 会自动检测这些信号(关键字目录 + 同名文件并存)。**只要 cat 8 命中,AI 第一件事不是动手,是问用户**:

> 看到你这有 `new/` / `backup/` / `dev/` 等几个目录,而且像 `Skill.xlsx` 这种文件在 `battle/` 和 `battle/new/` 都有 —— 先确认两件事:
> - **哪一个是当前线上 / 正式环境配置**(改动最终生效的那一份)?
> - 其他目录是什么?(历史备份 / 下一版开发 / 实验沙盒 / 别的?)
> 答完我把"正式环境配置路径"记到 `profile.md` 的 `baseline` 字段,下次自动应用。

**用户确认前,禁止改这些目录里的任何表** —— 误改备份 / 实验 / 旧版后果不一(有些会被同步覆盖、有些会进错版本、有些会被当真在用)。

落档后,`baseline` 字段就是"线上"的权威指针,后续任何"改一下 X 表"的指令默认指向它。

## 多版本配置管理(项目有 trunk + version_*/ 这种布局时)

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
   > - 这次任务针对的是 **哪个版本目录**?
   > 答完我记到 profile.md,以后不再问。

2. **候选回填永远同版本目录、同子路径**:改 `version_1.1/data/Skill.xlsx`,候选写到 `version_1.1/data/Skill_candidate.xlsx`(同目录,不是同版本根),**不跨版本**。绝不主动把改动写到 trunk 或别的版本目录。

3. **`--root` 传当前版本目录,不是 `<配置仓>` 根**:`inspect --root <配置仓>/version_1.1/` —— 这样 inspect 只扫当前版本,不会把 4 个版本同名表混在一起。Project Memory 会通过向上回溯找到 `<工程仓>/.ai-config-table/`。

4. **跨版本 merge / 回流是 VCS 的活,不是 skill 的活**:用户说"把 v1.1 改动同步到 trunk",AI 走两步:
   - (a) **批量列 diff(只读,允许)**:遍历 v1.1 下涉及的表,挨个 `diff_config_tables.py --source trunk/X --candidate version_1.1/X --output diffs/X.md`,汇总成一份清单交给用户
   - (b) **拒绝自动 merge / cherry-pick / 覆盖 trunk**:让用户走他们自己的 git/svn 工具按清单同步
   - 边界:**只读列 diff = 允许**,**任何写 trunk 的动作 = 拒绝**。

5. **项目记忆默认项目级**:`<工程仓>/.ai-config-table/` 跨版本共享(col2 备注列、行号引用这种是整项目成立)。极少数版本特有规则才下沉到版本目录的 `.ai-config-table/`;**inspect 第一版只读找到的第一个,不做叠加**。如果你判断某条规则真的只在某版本成立,问用户落到哪一层。

6. **改 trunk 高危**:trunk = 线上,用户没明示"改 trunk"前,**默认假设当前任务在某个 version_*/ 而不是 trunk**。如果用户没说,主动问一次。

## 另一种主流方案:分支独立仓 + CI 合并流水线

实战中除了"同仓多版本目录",另一种活在生产里的形态是 **每个分支用不同的表格仓库**,然后写自动合并流水线把分支表内容合并回开发分支。这种布局的特征:

- 配置仓 ≠ 单个目录,而是 **几个并列的 git/svn 仓**(`tables-trunk-svn` / `tables-version1.1-svn` 等),每个分支一份
- 项目记忆和 lua 检查 / lua 备份目录都需要 **每仓独立** —— 因为 hookscript 和检查上下文不同
- 合并由 CI 流水线做,不是策划手动

AI 在这种布局下要做的两件事:

1. **不要把多仓当成同仓多目录** —— 每个仓应该独立 `inspect`,`--memory-root` 分别指向各自仓里的 `.ai-config-table/`(或都指向工程仓的同一个,看团队约定;`profile.md` 里要写清楚)
2. **跨仓 merge / cherry-pick 仍然走 VCS / CI,不是 skill 的活** —— 跟上节的铁律 4 一致

两种方案对比:

| | 同仓多版本目录(trunk + version_*/) | 分支独立仓 + CI 合并 |
|---|---|---|
| 检查脚本 | 一套 | 每仓一套 |
| 项目记忆 | 一份在工程仓 | 一份在工程仓,或每仓一份 |
| 跨版本 diff | skill 内部命令直接做 | 需要先 clone 各仓再 diff |
| 适合 | 分支生命周期短、版本并行少 | 分支生命周期长、并行多 |

哪种都行,**第一次接入时问用户用的是哪种**,记到 profile.md。

## 反例 —— 看到自己写下面这种立刻停

- 用户说"改 X 表",AI 不问版本直接改了 `trunk/`(★ trunk = 线上,高危)
- 用户说"改 v1.1 的 X",AI 把候选写到 `trunk/` 或别的版本目录
- 用户说"同步到 trunk",AI 直接跨版本自动 merge(应该走 VCS,skill 只列 diff)
- 把 `.ai-config-table/` 写在 SVN 自动同步镜像里(下次 svn up 覆盖掉)
- 用户没明示哪个是线上源,AI 自己猜了 `trunk` / `main` / `live` 名字
- 默认 VCS 是 git,看到 svn 工作副本就建议"先 git init"(★ 不要绑 VCS)
- 在分支独立仓布局里把多仓当一棵树扫(应该每仓 inspect 一次)
