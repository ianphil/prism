# Data Model: Foundation Agent Framework + Ollama

## Entities

### AgentDecision

The structured output of a social agent's decision-making process. Represents what the agent chooses to do with a post in their feed.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `choice` | `Literal["LIKE", "REPLY", "RESHARE", "SCROLL"]` | Yes | — | The action the agent takes |
| `reason` | `str` | Yes | — | 1-3 sentence explanation of the agent's reasoning |
| `content` | `str \| None` | No | `None` | Generated text for REPLY/RESHARE; None for LIKE/SCROLL |

**Relationships:**
- Produced by one `SocialAgent` per `decide()` call
- Will be consumed by simulation state updates (Feature 3)

**Invariants:**
- `choice` must be one of the four valid values
- `content` must be non-empty when `choice` is `REPLY` or `RESHARE`
- `reason` must be non-empty

**Validation:**

```python
from pydantic import BaseModel, field_validator
from typing import Literal

class AgentDecision(BaseModel):
    choice: Literal["LIKE", "REPLY", "RESHARE", "SCROLL"]
    reason: str
    content: str | None = None

    @field_validator("content")
    @classmethod
    def content_required_for_reply_reshare(cls, v, info):
        choice = info.data.get("choice")
        if choice in ("REPLY", "RESHARE") and not v:
            raise ValueError(
                f"content is required when choice is {choice}"
            )
        return v
```

### LLMConfig

Configuration for the LLM client, loaded from YAML and validated at startup.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `provider` | `Literal["ollama"]` | Yes | `"ollama"` | LLM provider identifier |
| `host` | `str` | No | `"http://localhost:11434"` | Ollama server URL |
| `model_id` | `str` | Yes | `"mistral"` | Ollama model name |
| `temperature` | `float` | No | `0.7` | Sampling temperature |
| `max_tokens` | `int` | No | `512` | Maximum output tokens |
| `seed` | `int \| None` | No | `None` | Random seed for reproducibility |

**Invariants:**
- `host` must be a valid URL
- `temperature` must be between 0.0 and 2.0
- `max_tokens` must be positive
- `provider` is currently always `"ollama"` (extensible later)

### AgentProfile

Profile data for constructing a social agent. Lightweight for MVP; expanded in Feature 5 (Data Pipeline).

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `agent_id` | `str` | Yes | — | Unique identifier for the agent |
| `name` | `str` | Yes | — | Display name |
| `interests` | `list[str]` | Yes | — | Topics the agent cares about |
| `personality` | `str` | Yes | — | Brief personality description |

**Relationships:**
- One `AgentProfile` creates one `SocialAgent`
- Future: profiles generated from Twitter data (Feature 5)

**Invariants:**
- `agent_id` must be unique across the simulation
- `interests` must be non-empty
- `personality` must be non-empty

## State Transitions

### AgentDecision Lifecycle

```
LLM Response
    │
    ▼
┌──────────┐    response.value    ┌───────────────┐
│ Raw LLM  │ ───────────────────▶ │ AgentDecision │
│ Response  │    populated         │  (validated)  │
└──────────┘                      └───────────────┘
    │
    │ response.value is None
    ▼
┌──────────┐    JSON parse OK     ┌───────────────┐
│ Raw Text │ ───────────────────▶ │ AgentDecision │
│ Response │                      │  (validated)  │
└──────────┘                      └───────────────┘
    │
    │ JSON parse fails
    ▼
┌──────────────────────┐
│ Default: SCROLL      │
│ reason: parse error  │
│ content: None        │
└──────────────────────┘
```

| State | Description |
|-------|-------------|
| Raw LLM Response | Framework response object from `agent.run()` |
| AgentDecision (validated) | Successfully parsed and validated Pydantic model |
| Default SCROLL | Fallback when parsing fails; logged as warning |

## Data Flow

### Config → Client → Agent → Decision

```
configs/default.yaml
        │
        ▼ load_config()
    LLMConfig (validated)
        │
        ▼ create_llm_client()
    OllamaChatClient
        │
        ▼ create_agent()
    ChatAgent
        │
        ▼ SocialAgent(agent, profile)
    SocialAgent
        │
        ▼ decide(feed_text)
    AgentDecision
```

## Validation Summary

| Entity | Rule | Error |
|--------|------|-------|
| AgentDecision | `choice` in valid set | Pydantic validation error |
| AgentDecision | `content` required for REPLY/RESHARE | `ValueError` via field_validator |
| AgentDecision | `reason` non-empty | Pydantic validation error |
| LLMConfig | `temperature` in [0.0, 2.0] | Pydantic validation error |
| LLMConfig | `max_tokens` > 0 | Pydantic validation error |
| LLMConfig | `host` is valid URL | Pydantic validation error |
| AgentProfile | `interests` non-empty | Pydantic validation error |
| AgentProfile | `agent_id` unique | Enforced at simulation level (Feature 3) |
