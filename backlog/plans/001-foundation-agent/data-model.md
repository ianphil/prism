# Data Model: Foundation Agent Framework

## Entities

### Choice (Enum)

Possible agent actions for a post.

| Value | Description |
|-------|-------------|
| IGNORE | Skip the post, no interaction |
| LIKE | Like/favorite the post |
| REPLY | Write a reply to the post |
| RESHARE | Repost/retweet with optional comment |

### AgentDecision

The structured output from an agent's decision-making process.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| choice | Choice | Yes | - | The action the agent decided to take |
| reason | str | Yes | - | 1-2 sentence explanation of why |
| content | str \| None | No | None | Generated text for REPLY/RESHARE |
| post_id | str | Yes | - | ID of the post being acted upon |
| timestamp | datetime | No | now() | When the decision was made |

**Relationships:**
- References one Post (by post_id)
- Belongs to one SocialAgent (implicit via context)

**Invariants:**
- If choice is REPLY or RESHARE, content must not be None
- If choice is IGNORE or LIKE, content must be None
- reason must be non-empty string

### AgentProfile

Identity and characteristics of a social media agent.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| id | str | Yes | - | Unique agent identifier |
| name | str | Yes | - | Display name |
| interests | list[str] | Yes | [] | Topics the agent cares about |
| personality | str | No | "neutral" | Personality description |
| stance | dict[str, str] | No | {} | Positions on topics |

**Relationships:**
- Owns many AgentDecisions (via simulation context)

**Invariants:**
- id must be unique across simulation
- interests must have at least one item

### Post

A social media post that agents evaluate. Minimal version for foundation feature.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| id | str | Yes | - | Unique post identifier |
| author_id | str | Yes | - | ID of the posting agent |
| text | str | Yes | - | Post content |
| timestamp | datetime | Yes | - | When posted |
| has_media | bool | No | False | Whether post has visual content |
| media_type | str \| None | No | None | "image", "video", "gif" |
| media_description | str \| None | No | None | Description of visual |
| likes | int | No | 0 | Current like count |
| reshares | int | No | 0 | Current reshare count |
| replies | int | No | 0 | Current reply count |

**Relationships:**
- Belongs to one author (AgentProfile by author_id)
- Has many AgentDecisions (agents deciding on this post)

**Invariants:**
- If has_media is True, media_type must not be None
- Engagement counts (likes, reshares, replies) must be >= 0

### LLMConfig

Configuration for the LLM client.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| endpoint | str | Yes | "http://localhost:11434" | Ollama API endpoint |
| model | str | Yes | "mistral" | Model name to use |
| reasoning_effort | str | No | "medium" | low/medium/high |
| timeout | int | No | 30 | Request timeout in seconds |
| temperature | float | No | 0.7 | Sampling temperature |

**Invariants:**
- endpoint must be valid URL
- reasoning_effort must be one of: low, medium, high
- timeout must be > 0
- temperature must be between 0 and 2

## State Transitions

### AgentDecision Lifecycle

```
┌─────────┐
│ (start) │
└────┬────┘
     │ Agent receives feed
     ▼
┌─────────┐
│ Pending │  Agent is processing
└────┬────┘
     │ LLM returns response
     ▼
┌─────────┐
│ Parsed  │  Response parsed to decision
└────┬────┘
     │ Validation passes
     ▼
┌─────────┐
│ Valid   │  Decision ready for use
└─────────┘
```

| State | Description |
|-------|-------------|
| Pending | Agent is making inference |
| Parsed | Raw response converted to structure |
| Valid | All invariants satisfied |

### Error States

```
┌─────────┐
│ Pending │
└────┬────┘
     │ Timeout / Error
     ▼
┌─────────┐
│ Failed  │  Decision could not be made
└─────────┘

┌─────────┐
│ Parsed  │
└────┬────┘
     │ Validation fails
     ▼
┌─────────┐
│ Invalid │  Response doesn't match schema
└─────────┘
```

## Data Flow

### Agent Decision Flow

```
┌──────────────┐
│ list[Post]   │  Feed input
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ SocialAgent  │
│  .decide()   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ AgentProfile │  Loaded for prompt
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Prompt     │  System + User messages
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   LLM        │  Ollama inference
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Parse      │  Extract JSON from response
└──────┬───────┘
       │
       ▼
┌──────────────┐
│AgentDecision │  Validated output
└──────────────┘
```

## Validation Summary

| Entity | Rule | Error |
|--------|------|-------|
| AgentDecision | choice is valid Choice | ValueError |
| AgentDecision | content matches choice type | ValueError |
| AgentDecision | reason is non-empty | ValueError |
| AgentProfile | id is non-empty | ValueError |
| AgentProfile | interests has >= 1 item | ValueError |
| Post | has_media implies media_type | ValueError |
| Post | engagement counts >= 0 | ValueError |
| LLMConfig | valid endpoint URL | ValidationError |
| LLMConfig | reasoning_effort in allowed values | ValidationError |

## JSON Schema (for LLM prompts)

### AgentDecision Response Format

```json
{
  "type": "object",
  "properties": {
    "choice": {
      "type": "string",
      "enum": ["IGNORE", "LIKE", "REPLY", "RESHARE"]
    },
    "reason": {
      "type": "string",
      "minLength": 1
    },
    "content": {
      "type": ["string", "null"]
    },
    "post_id": {
      "type": "string"
    }
  },
  "required": ["choice", "reason", "post_id"]
}
```

This schema is embedded in the agent prompt to guide structured output.
