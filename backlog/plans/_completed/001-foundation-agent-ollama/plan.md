# Plan: Foundation Agent Framework + Ollama Integration

## Summary

Establish PRISM's core agent infrastructure by integrating Microsoft Agent Framework's `OllamaChatClient` and `ChatAgent` with a config-driven `SocialAgent` that produces structured `AgentDecision` outputs. This is the foundational layer that all other PRISM features build upon.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    PRISM Foundation                  │
│                                                     │
│  configs/default.yaml                               │
│         │                                           │
│         ▼                                           │
│  ┌─────────────┐                                    │
│  │ LLMConfig   │  (Pydantic validated YAML)         │
│  └──────┬──────┘                                    │
│         │                                           │
│         ▼                                           │
│  ┌──────────────────┐                               │
│  │ OllamaChatClient │  (from agent-framework)       │
│  │  host, model_id  │                               │
│  └────────┬─────────┘                               │
│           │ create_agent()                           │
│           ▼                                         │
│  ┌──────────────┐     ┌────────────────┐            │
│  │  ChatAgent   │────▶│  SocialAgent   │            │
│  │ (framework)  │     │   (PRISM)      │            │
│  └──────────────┘     └───────┬────────┘            │
│                               │ decide(feed_text)   │
│                               ▼                     │
│                       ┌───────────────┐             │
│                       │ AgentDecision │             │
│                       │ choice/reason │             │
│                       │ /content      │             │
│                       └───────────────┘             │
└─────────────────────────────────────────────────────┘
```

## Detailed Architecture

```
User Code
    │
    ▼
SocialAgent(agent_id, name, interests, personality, config)
    │
    ├── Builds system prompt from profile + template
    │
    ├── Creates ChatAgent via OllamaChatClient.create_agent()
    │       │
    │       ├── name = agent_id
    │       ├── instructions = system_prompt
    │       ├── response_format = AgentDecision
    │       ├── temperature = config.temperature
    │       └── max_tokens = config.max_tokens
    │
    └── decide(feed_text: str) -> AgentDecision
            │
            ├── await self._agent.run(feed_text)
            │
            ├── response.value → AgentDecision (structured)
            │
            └── Fallback: parse response.text as JSON if .value is None
```

### Component Responsibilities

| Component | Role | Integrates With |
|-----------|------|-----------------|
| `LLMConfig` | Validates and holds LLM configuration | YAML files, env vars |
| `create_llm_client()` | Constructs `OllamaChatClient` from config | `LLMConfig`, agent-framework |
| `SocialAgent` | Social media decision agent | `ChatAgent`, prompt templates |
| `AgentDecision` | Structured output model | Pydantic, LLM response |
| `build_system_prompt()` | Renders agent personality into instructions | Profile data, template strings |
| `build_feed_prompt()` | Formats post feed for agent consumption | Feed data, template strings |

### Data Flow: Agent Decision

```
1. Load config ─── configs/default.yaml ──▶ LLMConfig
2. Create client ─ LLMConfig ──▶ OllamaChatClient
3. Create agent ── OllamaChatClient.create_agent(
                       name, instructions, response_format
                   ) ──▶ ChatAgent
4. Wrap agent ──── ChatAgent ──▶ SocialAgent
5. Decide ──────── SocialAgent.decide(feed_text)
                       │
                       ├── await agent.run(feed_text)
                       ├── response.value → AgentDecision
                       └── return AgentDecision
```

## File Structure

```
prism/
├── __init__.py                    # MODIFY: add version
├── llm/
│   ├── __init__.py                # NEW: exports
│   ├── client.py                  # NEW: create_llm_client() factory
│   └── config.py                  # NEW: LLMConfig Pydantic model
├── agents/
│   ├── __init__.py                # NEW: exports
│   ├── social_agent.py            # NEW: SocialAgent class
│   ├── decision.py                # NEW: AgentDecision model
│   └── prompts.py                 # NEW: prompt templates
configs/
├── default.yaml                   # NEW: default configuration
tests/
├── __init__.py
├── llm/
│   ├── __init__.py                # NEW
│   ├── test_config.py             # NEW: config validation tests
│   └── test_client.py             # NEW: client creation tests
├── agents/
│   ├── __init__.py                # NEW
│   ├── test_decision.py           # NEW: decision model tests
│   ├── test_prompts.py            # NEW: prompt template tests
│   └── test_social_agent.py       # NEW: social agent tests
```

## Critical: Structured Output Fallback

**Problem**: Not all Ollama models support native `response_format` with Pydantic schemas. The `mistral` model (our dev default) may return plain text instead of structured JSON.

**Solution**: Two-layer parsing strategy:

1. **Primary**: Use `response_format=AgentDecision` on `agent.run()`. If `response.value` is populated, use it directly.
2. **Fallback**: If `response.value` is `None`, attempt to parse `response.text` as JSON into `AgentDecision`. The prompt template explicitly requests JSON output as a belt-and-suspenders approach.
3. **Last resort**: If both fail, return a default `AgentDecision(choice="SCROLL", reason="Failed to parse LLM output", content=None)` and log a warning.

## Implementation Phases

### Phase 1: Data Models and Configuration
- `AgentDecision` Pydantic model
- `LLMConfig` Pydantic model
- `configs/default.yaml`
- Config loading and validation

### Phase 2: LLM Client
- `create_llm_client()` factory function
- `OllamaChatClient` construction from config
- Connection validation

### Phase 3: Agent Layer
- Prompt templates (system + user)
- `SocialAgent` class with `decide()` method
- Structured output with fallback parsing

### Phase 4: Integration Validation
- End-to-end test with mocked LLM
- Integration test with real Ollama (optional, marked)

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Config format | YAML + Pydantic validation | Human-readable, validated at load time, per PRD |
| Package | `agent-framework-ollama --pre` | Minimal deps; includes core + Ollama only |
| Agent creation | `client.create_agent()` convenience | Cleaner than manual `ChatAgent(chat_client=...)` |
| Structured output | `response_format=AgentDecision` | First-class Pydantic support in framework |
| Fallback parsing | JSON from response text | Handles models without native structured output |
| Default model | `mistral` | Fast iteration; `gpt-oss:20b` may not be available |
| Async | `async def decide()` | Matches framework; enables future parallelism |
| Choice enum | `Literal["LIKE", "REPLY", "RESHARE", "SCROLL"]` | Simple, extensible, matches PRD |

## Configuration Example

```yaml
# configs/default.yaml
llm:
  provider: ollama
  host: "http://localhost:11434"
  model_id: mistral
  temperature: 0.7
  max_tokens: 512
  seed: null  # Set for reproducibility
```

## Files to Modify

| File | Change |
|------|--------|
| `prism/__init__.py` | Add `__version__` |
| `pyproject.toml` | Dependencies added via `uv add` (not manual edit) |

## New Files

| File | Purpose |
|------|---------|
| `prism/llm/__init__.py` | Package exports |
| `prism/llm/config.py` | `LLMConfig` Pydantic model + `load_config()` |
| `prism/llm/client.py` | `create_llm_client()` factory |
| `prism/agents/__init__.py` | Package exports |
| `prism/agents/decision.py` | `AgentDecision` Pydantic model |
| `prism/agents/prompts.py` | System/user prompt templates |
| `prism/agents/social_agent.py` | `SocialAgent` class |
| `configs/default.yaml` | Default LLM configuration |
| `tests/llm/__init__.py` | Test package |
| `tests/llm/test_config.py` | Config validation tests |
| `tests/llm/test_client.py` | Client creation tests |
| `tests/agents/__init__.py` | Test package |
| `tests/agents/test_decision.py` | Decision model tests |
| `tests/agents/test_prompts.py` | Prompt template tests |
| `tests/agents/test_social_agent.py` | Social agent tests |

## Verification

1. `uv run pytest` — all tests pass
2. `uv run ruff check . && uv run flake8 . && uv run black --check .` — linting clean
3. Integration test (requires running Ollama): agent produces valid `AgentDecision` from mock feed

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Agent Framework beta API changes | Pin version; wrap behind `SocialAgent` interface |
| Structured output fails for Ollama models | Fallback JSON parsing from prompt-guided text |
| `gpt-oss:20b` unavailable | Default to `mistral`; model is config-driven |
| Ollama not running during tests | Mock `OllamaChatClient` in unit tests; separate integration tests |

## Limitations (MVP)

1. **No conversation history** — Each `decide()` call is stateless. Multi-round memory is a future feature.
2. **No tool calling** — Agent receives feed as text, not via RAG tool. Tool integration comes with Feature 2.
3. **No parallelism** — Single agent at a time. Batch execution comes with Feature 3.
4. **No tracing** — OpenTelemetry integration deferred to Feature 6.
5. **No CLI** — Configuration is code/YAML only. CLI comes with Feature 7.

## References

- [Agent Framework PyPI](https://pypi.org/project/agent-framework/)
- [OllamaChatClient API](https://learn.microsoft.com/es-es/python/api/agent-framework-core/agent_framework.ollama.ollamachatclient)
- [ChatClientAgent Docs](https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-types/chat-client-agent)
- [Structured Output Tutorial](https://learn.microsoft.com/en-us/agent-framework/tutorials/agents/structured-output)
- [Ollama Samples](https://github.com/microsoft/agent-framework/tree/main/python/samples/getting_started/agents/ollama)
