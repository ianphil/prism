# Foundation: Agent Framework + Ollama — Analysis

## Executive Summary

This feature establishes PRISM's core infrastructure: integrating Microsoft Agent Framework (Python) with Ollama for local LLM inference. Every subsequent feature (RAG, simulation loop, experiments) depends on this foundation layer.

| Pattern | Integration Point |
|---------|-------------------|
| Chat client abstraction (`IChatClient`) | LLM provider flexibility (Ollama, Azure, OpenAI) |
| Structured output (`response_format`) | Agent decision as Pydantic model (`AgentDecision`) |
| Async agent invocation (`agent.run()`) | Non-blocking agent decisions for future parallelism |
| YAML-driven configuration | Model selection, endpoint, temperature per environment |

## Architecture Comparison

### Current Architecture

```
prism/
├── __init__.py          # Empty docstring
main.py                  # Stub: print("Hello from prism!")
pyproject.toml           # Skeleton: no runtime deps, dev tooling only
configs/                 # (does not exist yet)
```

No runtime code, no dependencies, no agent infrastructure.

### Target Architecture

```
prism/
├── __init__.py
├── llm/
│   ├── __init__.py
│   ├── client.py            # ChatClient protocol + OllamaChatClient wrapper
│   └── config.py            # LLM configuration (model, endpoint, params)
├── agents/
│   ├── __init__.py
│   ├── social_agent.py      # SocialAgent wrapping ChatAgent
│   ├── decision.py          # AgentDecision Pydantic model
│   └── prompts.py           # Prompt templates for social agent decisions
configs/
├── default.yaml             # Default configuration
tests/
├── test_llm_client.py
├── test_social_agent.py
├── test_decision.py
├── test_config.py
```

## Pattern Mapping

### 1. Chat Client Abstraction

**Current Implementation:** None.

**Target Evolution:** Wrap `OllamaChatClient` from `agent-framework-ollama` behind a thin configuration layer. The framework already provides `IChatClient` protocol conformance, so our wrapper focuses on configuration loading (YAML → constructor params) rather than reimplementing the interface.

```python
# Framework provides:
from agent_framework.ollama import OllamaChatClient

# We add: config-driven construction
client = OllamaChatClient(host=config.endpoint, model_id=config.model)
```

### 2. Agent Pattern (ChatAgent)

**Current Implementation:** None.

**Target Evolution:** `SocialAgent` wraps `ChatAgent` (created via `OllamaChatClient.create_agent()`) with social-media-specific prompt templates and structured output via `response_format=AgentDecision`.

```python
# Framework provides:
agent = client.create_agent(
    name="agent_123",
    instructions=prompt,
    response_format=AgentDecision,
    temperature=0.7,
)
result = await agent.run(feed_text)
decision = result.value  # AgentDecision instance
```

### 3. Structured Output

**Current Implementation:** None.

**Target Evolution:** Define `AgentDecision` as a Pydantic `BaseModel` with choice/reason/content fields. Pass as `response_format` to `agent.run()`, access via `result.value`.

### 4. Configuration

**Current Implementation:** No config files.

**Target Evolution:** YAML config loaded with PyYAML/Pydantic, validated into typed dataclass. Supports model selection, endpoint override, temperature/seed/max_tokens.

## What Exists vs What's Needed

### Currently Built

| Component | Status | Notes |
|-----------|--------|-------|
| Project skeleton | ✅ | `pyproject.toml`, `prism/__init__.py`, dev tooling |
| Dev tooling | ✅ | ruff, black, flake8, pytest configured |
| Planning docs | ✅ | PRD, implementation order, quick plans |

### Needed

| Component | Status | Source |
|-----------|--------|--------|
| `agent-framework-ollama` dependency | ❌ | `uv add agent-framework-ollama --pre` |
| `pyyaml` dependency | ❌ | `uv add pyyaml` |
| `pydantic` dependency | ❌ | `uv add pydantic` |
| LLM client wrapper (`prism/llm/`) | ❌ | Thin config layer over framework |
| Social agent (`prism/agents/`) | ❌ | ChatAgent + prompt template |
| Decision model (`AgentDecision`) | ❌ | Pydantic BaseModel |
| Prompt templates | ❌ | Social media decision prompts |
| YAML config (`configs/default.yaml`) | ❌ | Model/endpoint/params |
| Integration tests | ❌ | Agent makes valid decision |

## Key Insights

### What Works Well

1. **Microsoft Agent Framework API is stable enough.** The `OllamaChatClient` has a clean constructor (`host`, `model_id`) and convenience `create_agent()` method that handles wiring. Beta releases are frequent (weekly).
2. **Structured output is first-class.** `response_format=BaseModel` on `agent.run()` returns typed Pydantic instances via `result.value`. This eliminates manual JSON parsing for agent decisions.
3. **Async-native design.** All agent operations are `async`, which aligns with future parallelization needs (batching 250+ agent decisions).
4. **`OllamaChatClient` is in `agent-framework-core`.** The `OllamaChatClient` class lives in the core package (import path: `agent_framework.ollama.OllamaChatClient`), so we may only need `agent-framework-core` or the selective `agent-framework-ollama` package.

### Gaps/Limitations

| Limitation | Solution |
|------------|----------|
| `agent-framework` is in preview (beta) | Pin version in `pyproject.toml`, wrap behind our own interfaces |
| `gpt-oss:20b` may not exist in Ollama registry yet | Use `mistral` for dev/testing; make model configurable |
| Structured output may not work with all Ollama models | Test with `mistral` and `qwen2.5`; fall back to prompt-based JSON parsing |
| No `configs/` directory exists | Create `configs/default.yaml` |
| `agent-framework-ollama` install path unclear | Research: may be `uv add agent-framework --pre` (meta) or `uv add agent-framework-ollama --pre` (selective) |
