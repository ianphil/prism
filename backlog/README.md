# Backlog

Project backlog for managing plans, issues, and bugs.

## Structure

- `plans/` - Feature plans, roadmap items, larger initiatives
- `issues/` - General tasks, improvements, tech debt
- `bugs/` - Defects, broken functionality
- `_templates/` - Markdown templates for each type

## Conventions

### File Naming

Use the pattern: `YYYYMMDD-short-description.md`

Example: `20260127-add-user-authentication.md`

### Frontmatter

All items should include YAML frontmatter:

```yaml
---
title: "Short descriptive title"
status: open | in-progress | done | closed
priority: low | medium | high | critical
created: YYYY-MM-DD
---
```

### Status Values

- `open` - Not yet started
- `in-progress` - Actively being worked on
- `done` - Completed
- `closed` - Closed without completion (duplicate, won't fix, etc.)

### Priority Values

- `critical` - Must be addressed immediately
- `high` - Important, should be addressed soon
- `medium` - Normal priority
- `low` - Nice to have, address when time permits
