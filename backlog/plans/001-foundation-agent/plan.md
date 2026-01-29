# Plan: Foundation Agent Framework + Ollama Integration

## Summary

Implement the core agent infrastructure for PRISM: an `OllamaChatClient` for LLM inference, a `SocialAgent` class for social media decision-making, structured output via `AgentDecision`, and YAML-driven configuration. This enables all downstream features.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     PRISM Foundation                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐     ┌──────────────┐     ┌─────────────┐ │
│  │   Config     │────▶│  LLM Client  │────▶│   Ollama    │ │
│  │  (YAML)      │     │  (IChatClient)│     │  (local)    │ │
│  └──────────────┘     └──────┬───────┘     └─────────────┘ │
│                              │                              │
│                              ▼                              │
│                    ┌──────────────────┐                     │
│                    │   SocialAgent    │                     │
│                    │  ┌────────────┐  │                     │
│                    │  │  Profile   │  │                     │
│                    │  │  Prompts   │  │                     │
│                    │  └────────────┘  │                     │
│                    └────────┬─────────┘                     │
│                             │                               │
│                             ▼                               │
│                    ┌──────────────────┐                     │
│                    │  AgentDecision   │                     │
│                    │  (choice/reason/ │                     │
│                    │   content)       │                     │
│                    └──────────────────┘                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Detailed Architecture

```
                    ┌─────────────────┐
                    │  configs/       │
                    │  default.yaml   │
                    └────────┬────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    prism/config/settings.py                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  @dataclass                                          │    │
│  │  class LLMConfig:                                    │    │
│  │      endpoint: str                                   │    │
│  │      model: str                                      │    │
│  │      reasoning_effort: str                           │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    prism/llm/client.py                       │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  class OllamaChatClient:                             │    │
│  │      def __init__(config: LLMConfig)                │    │
│  │      async def chat(messages) -> str                │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                 prism/agents/social_agent.py                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  class SocialAgent:                                  │    │
│  │      def __init__(profile, client)                  │    │
│  │      async def decide(feed) -> AgentDecision        │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                 prism/agents/decisions.py                    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  class Choice(Enum):                                 │    │
│  │      IGNORE, LIKE, REPLY, RESHARE                   │    │
│  │                                                      │    │
│  │  @dataclass                                          │    │
│  │  class AgentDecision:                                │    │
│  │      choice: Choice                                  │    │
│  │      reason: str                                     │    │
│  │      content: str | None                            │    │
│  │      post_id: str                                   │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Role | Integrates With |
|-----------|------|-----------------|
| `LLMConfig` | Holds LLM settings | Config loader, OllamaChatClient |
| `OllamaChatClient` | Makes LLM requests | Ollama REST API |
| `SocialAgent` | Wraps LLM for social decisions | OllamaChatClient, Prompts |
| `AgentDecision` | Structured decision output | SocialAgent, Simulation (future) |
| `AgentProfile` | Agent identity/interests | SocialAgent |

### Data Flow: Agent Decision

```
Feed (list[Post])
       │
       ▼
┌──────────────────┐
│  SocialAgent     │
│  .decide(feed)   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Build prompt:   │
│  - System: profile│
│  - User: feed    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ OllamaChatClient │
│  .chat(messages) │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Ollama REST API │
│  /api/chat       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Parse response  │
│  → AgentDecision │
└────────┬─────────┘
         │
         ▼
   AgentDecision
```

## File Structure

```
prism/
├── __init__.py                    # MODIFY: Add version
├── agents/
│   ├── __init__.py                # NEW
│   ├── social_agent.py            # NEW: SocialAgent class
│   ├── decisions.py               # NEW: AgentDecision, Choice enum
│   ├── profiles.py                # NEW: AgentProfile dataclass
│   └── prompts.py                 # NEW: Prompt templates
├── llm/
│   ├── __init__.py                # NEW
│   ├── client.py                  # NEW: OllamaChatClient
│   └── config.py                  # NEW: LLMConfig
├── config/
│   ├── __init__.py                # NEW
│   └── settings.py                # NEW: Config loading
└── models/
    ├── __init__.py                # NEW
    └── post.py                    # NEW: Post dataclass (minimal for testing)

configs/
└── default.yaml                   # NEW: Default configuration

tests/
├── __init__.py                    # NEW
├── agents/
│   ├── __init__.py                # NEW
│   ├── test_social_agent.py       # NEW
│   └── test_decisions.py          # NEW
├── llm/
│   ├── __init__.py                # NEW
│   └── test_client.py             # NEW
└── conftest.py                    # NEW: Shared fixtures
```

## Critical: Agent Framework Dependency

**Problem**: The PRD references Microsoft Agent Framework, but the Python SDK may not exist or may have different APIs than expected.

**Solution**:
1. First attempt to use Agent Framework if available
2. If not available, implement our own abstractions directly
3. Use Ollama REST API directly - well documented and stable
4. Our `OllamaChatClient` provides the same interface regardless

This makes the implementation resilient to Agent Framework availability.

## Implementation Phases

See `tasks.md` for detailed TDD breakdown. Overview:

1. **Phase 1: Core Data Models** - AgentDecision, Choice, AgentProfile, Post
2. **Phase 2: LLM Client** - OllamaChatClient with Ollama REST API
3. **Phase 3: Configuration** - YAML loading, LLMConfig
4. **Phase 4: Agent Implementation** - SocialAgent, prompts
5. **Phase 5: Integration** - End-to-end test with mock feed

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Direct Ollama REST | Don't depend on Agent Framework | More reliable, well-documented |
| Async/await | All I/O operations | Enables future parallelism |
| Pydantic for config | Validation + typing | Standard Python practice |
| dataclass for models | Simple, fast | No ORM overhead needed |
| httpx for HTTP | Async support, modern | Better than requests for async |

## Configuration Example

`configs/default.yaml`:
```yaml
llm:
  endpoint: "http://localhost:11434"
  model: "mistral"  # Use "llama3:70b" for quality
  reasoning_effort: "medium"
  timeout: 30

agent:
  default_personality: "curious and engaged social media user"

logging:
  level: "INFO"
```

## Files to Modify

| File | Change |
|------|--------|
| `prism/__init__.py` | Add `__version__` |
| `pyproject.toml` | Add runtime dependencies |

## New Files

| File | Purpose |
|------|---------|
| `prism/agents/social_agent.py` | Main agent class |
| `prism/agents/decisions.py` | Decision types and structures |
| `prism/agents/profiles.py` | Agent identity |
| `prism/agents/prompts.py` | Prompt building |
| `prism/llm/client.py` | Ollama HTTP client |
| `prism/llm/config.py` | LLM configuration |
| `prism/config/settings.py` | YAML config loader |
| `prism/models/post.py` | Post data model |
| `configs/default.yaml` | Default config |

## Verification

1. Unit tests pass: `uv run pytest tests/`
2. Lint passes: `uv run ruff check . && uv run flake8 .`
3. Integration test: Agent makes valid decision from mock feed
4. Config test: Can switch models via YAML

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Ollama not running | Skip integration tests, mock in unit tests |
| Model not available | Use `mistral` as fallback |
| Response parsing fails | Robust regex + fallback defaults |
| Slow inference | Timeout + async for non-blocking |

## Limitations (MVP)

1. Single model support (no hot-swapping during runtime)
2. No conversation memory (stateless decisions)
3. No retry logic (simple timeout)
4. Mock feed only (no RAG integration)

## References

- [Ollama API Documentation](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [PRISM PRD v1.2](../../aidocs/prd.md)
- [httpx Documentation](https://www.python-httpx.org/)
