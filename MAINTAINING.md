# 维护说明(给作者自己看)

改完文件,3 条命令推上去:

```bash
git add -A && git commit -m "描述这次改了什么"
git push
git tag vX.Y && git push --tags    # 只有切发布版本才打 tag
```

如果工作流或脚本有让下游需要感知的变化,改 `SKILL.md` 顶部 YAML frontmatter 里的 `version:` 字段。git tag(`vX.Y`)才是对用户公开的版本钉。
