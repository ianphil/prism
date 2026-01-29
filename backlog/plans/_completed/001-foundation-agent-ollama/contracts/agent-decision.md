# Agent Decision Contract

## Overview

`AgentDecision` is the structured output of a social agent's decision-making. It represents what the agent chooses to do with a post in their feed.

## Schema

```python
# prism/agents/decision.py

from pydantic import BaseModel, field_validator
from typing import Literal

class AgentDecision(BaseModel):
    """Structured output of a social agent's decision."""

    choice: Literal["LIKE", "REPLY", "RESHARE", "SCROLL"]
    reason: str
    content: str | None = None
```

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `choice` | `"LIKE" \| "REPLY" \| "RESHARE" \| "SCROLL"` | Yes | The action taken |
| `reason` | `str` | Yes | 1-3 sentence reasoning |
| `content` | `str \| None` | Conditional | Generated text for REPLY/RESHARE |

## Validation Rules

1. `choice` must be one of: `LIKE`, `REPLY`, `RESHARE`, `SCROLL`
2. `reason` must be non-empty
3. `content` must be non-empty when `choice` is `REPLY` or `RESHARE`
4. `content` may be `None` when `choice` is `LIKE` or `SCROLL`

## JSON Schema

```json
{
  "type": "object",
  "properties": {
    "choice": {
      "type": "string",
      "enum": ["LIKE", "REPLY", "RESHARE", "SCROLL"]
    },
    "reason": {
      "type": "string",
      "minLength": 1
    },
    "content": {
      "type": ["string", "null"]
    }
  },
  "required": ["choice", "reason"]
}
```

## Examples

### LIKE

```json
{
  "choice": "LIKE",
  "reason": "This aligns with my interest in cryptocurrency adoption trends.",
  "content": null
}
```

### REPLY

```json
{
  "choice": "REPLY",
  "reason": "I want to share my own experience with Bitcoin payments at local shops.",
  "content": "That's great to hear! My favorite bookstore started accepting Bitcoin last month too. The payment experience was seamless."
}
```

### RESHARE

```json
{
  "choice": "RESHARE",
  "reason": "This is important news that my followers interested in tech adoption would want to see.",
  "content": "More local businesses adopting crypto payments - this is the kind of grassroots adoption we need to see."
}
```

### SCROLL

```json
{
  "choice": "SCROLL",
  "reason": "This post about gardening tips doesn't align with my interests.",
  "content": null
}
```
