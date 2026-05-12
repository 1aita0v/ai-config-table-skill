# Maintaining (for the author)

Three lines to publish an update after editing files in this repo:

```bash
git add -A && git commit -m "describe the change"
git push
git tag vX.Y && git push --tags    # only when cutting a release
```

Bump `version:` in `SKILL.md`'s YAML frontmatter when the workflow or scripts change in a way downstream installs need to notice. The git tag (`vX.Y`) is the public, user-facing version pin.
