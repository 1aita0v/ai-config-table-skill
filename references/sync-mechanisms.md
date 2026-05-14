# `.ai-config-table/` 同步机制 + 跨人入档时序

skill **只负责把项目记忆写到稳定路径**(`<工程仓>/.ai-config-table/`)。**怎么 round-trip 给同事是团队的事,skill 不绑定 VCS**。

## 入档命令对照表

| VCS / 同步机制 | 入档命令 | 备注 |
|---|---|---|
| **git** | `git add .ai-config-table/ && git commit -m "..." && git push` | 最常见,跟代码一起走 |
| **svn**(单仓 SVN 项目) | `svn add .ai-config-table/ && svn ci -m "..."` | SVN 工作副本,在工程仓根加进版本控制 |
| **Dropbox / 坚果云 / OneDrive** | 不用命令,**自动双向同步** | 有同名文件冲突时同步工具会生成 `.conflict.<host>` 副本,要手解 |
| **共享盘 (SMB/NFS)** | 不用命令,直接落盘共享 | 多人同时写有覆盖风险,**约定一个人负责入档**比抢着写稳 |
| **邮件 / IM 发包** | 手动 zip 发,接收方解到 `<工程仓>/` | 最原始,小团队 OK |
| **不同步**(个人本地) | `.gitignore` / `.svnignore` 加上 `.ai-config-table/` | 私人笔记,不分享 |

**skill 不替用户挑、不绑 git**。入档时问一次:"这条要团队共享(进 VCS / 走 Dropbox)还是只你本地用?",照用户选的走。

## 跨人入档时序约定

多人同时入档容易 git merge conflict / Dropbox 冲突副本。最低约束:

1. **topic 用稳定 slug**(英文小写 + 短横线 + 项目内唯一前缀,例 `lockey-rule` / `gamedev-resource-row-index`),不用纯中文长 topic。冲突时方便 grep 定位。

2. **AI 不主动 `git commit`,只 `git add` + 提示用户**。一句话告诉用户"我 append 完了,要 commit 你来",commit 时点和 message 由用户决定 —— 避免 AI 把 WIP 改动一锅端 commit 掉。

3. **冲突由用户手解**:`learned-patterns.md` 是纯 Markdown,git merge 失败时 100% 能手动 resolve(双方的 entry 顺序 / 重复都不致命)。AI 看到冲突时**停下**,把冲突段贴给用户,问"两条都留 / 留哪条"。

4. **同 topic 二次入档 = 修订前一条**:不要在 `learned-patterns.md` 留 2 个同名 topic 还差异冲突。要么写"修订:旧 → 新",要么直接编辑前一条。

## 反例

- AI 自作主张 `git commit -am "auto-save memory"` —— 用户可能正在改别的代码,会被一锅端
- topic 用 "记录一下技能 ID 段语义" 这种长中文 —— 冲突 grep 不到、merge 时不知道该留哪个
- 看到 git merge conflict 自己尝试 resolve —— learned-patterns.md 内容由用户拍板,AI resolve 等于擅自删/合并别人的记忆
- 同一条规则 append 两次 —— 第二次应该是修订前一条,不是再加一份
