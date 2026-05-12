# Project Config Profile Template

Use this template when a project has no existing AI-readable configuration map.

```markdown
# {Project} Config Profile

## Source

- Source of truth:
- Access method:
- Config root, export path, platform project ID, or table source:
- Export/build pipeline:
- Writeback policy:

## Table Layout

- Workbook/file patterns:
- Sheet naming rules:
- Header row:
- Data start row:
- Comment/metadata rows:
- Empty row behavior:
- Formula/style conventions:

## Key Rules

- Primary key fields:
- ID allocation method:
- ID reuse policy:
- Delete/deprecate policy:
- Enum/dictionary source:

## Cross-Table References

| From | Field | To | Required | Notes |
|---|---|---|---|---|
|  |  |  |  |  |

## Support Tables

| Purpose | Table/Sheet | Key Fields | When Required |
|---|---|---|---|
| Localization |  |  |  |
| Prompt/Error text |  |  |  |
| Resources/Icon/Audio/Effect |  |  |  |
| Items/Rewards |  |  |  |
| Conditions/Unlock |  |  |  |
| Guide/Jump/Entry |  |  |  |

## Validation Commands

```bash
```

## Known Risks

- 

## Open Questions

- 
```
