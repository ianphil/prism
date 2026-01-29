# Foundation Agent Framework Analysis

## Executive Summary

| Pattern | Integration Point |
|---------|-------------------|
| LLM Abstraction | `IChatClient` interface from Agent Framework |
| Agent Architecture | `ChatAgent` wrapper for social media decisions |
| Configuration | YAML-driven model/endpoint selection |
| Structured Output | Pydantic models for agent decisions |

This feature establishes the foundational layer for PRISM. All other features (RAG, simulation loop, experiments) depend on having working LLM-powered agents that can make decisions using gpt-oss:20b via Ollama.

## Architecture Comparison

### Current Architecture

```
prism/
└── __init__.py  # Empty package
```

The codebase is greenfield - no existing agent infrastructure.

### Target Architecture

```
prism/
├── __init__.py
├── agents/
│   ├── __init__.py
│   ├── social_agent.py      # SocialAgent wrapping ChatAgent
│   ├── prompts.py           # Decision prompt templates
│   └── decisions.py         # AgentDecision dataclass
├── llm/
│   ├── __init__.py
│   ├── client.py            # OllamaChatClient implementation
│   └── config.py            # LLM configuration
└── config/
    ├── __init__.py
    └── settings.py          # YAML config loader
```

## Pattern Mapping

### 1. IChatClient Abstraction

**Current Implementation:** None

**Target Evolution:**
- Implement `OllamaChatClient` conforming to Agent Framework's `IChatClient`
- Support both gpt-oss:20b (primary) and Mistral 7B (dev)
- Configure via YAML for endpoint, model, and reasoning effort

### 2. Agent Decision Pattern

**Current Implementation:** None

**Target Evolution:**
- `SocialAgent` class wrapping `ChatAgent`
- Structured output: Choice-Reason-Content triplets
- Decision types: IGNORE, LIKE, REPLY, RESHARE

### 3. Prompt Template Pattern

**Current Implementation:** None

**Target Evolution:**
- System prompt with agent profile (interests, personality)
- User prompt with feed context and media indicators
- Constrained action space for reproducibility

## What Exists vs What's Needed

### Currently Built

| Component | Status | Notes |
|-----------|--------|-------|
| Project skeleton | ✅ | pyproject.toml, basic structure |
| uv tooling | ✅ | Dev dependencies configured |
| Empty prism package | ✅ | Just __init__.py |

### Needed

| Component | Status | Source |
|-----------|--------|--------|
| OllamaChatClient | ❌ | Agent Framework IChatClient pattern |
| SocialAgent | ❌ | PRD §4.1 agent design |
| AgentDecision | ❌ | PRD structured output spec |
| Prompt templates | ❌ | PRD prompt design |
| YAML config | ❌ | Standard Python config pattern |
| Integration test | ❌ | Validate end-to-end |

## Key Insights

### What Works Well

1. **Agent Framework provides solid foundation** - IChatClient abstraction, ChatAgent base class, structured outputs
2. **Ollama local inference** - gpt-oss:20b benchmarked at ~3.1s/inference on M3 Ultra
3. **Clear PRD requirements** - Well-defined agent behavior and decision structure

### Gaps/Limitations

| Limitation | Solution |
|------------|----------|
| Agent Framework Python is preview | Pin version, maintain abstraction layer |
| gpt-oss:20b may not exist | Research actual Ollama model availability |
| No existing patterns in codebase | Follow PRD Appendix D structure |

## Open Questions Resolved

<!-- ASSUMPTION: Agent Framework Python package is available as 'agent-framework' via pip. Will verify during implementation and adjust if needed. -->

<!-- ASSUMPTION: gpt-oss:20b refers to a hypothetical model name from the PRD. Will use an actual available Ollama model (likely llama3 or mistral) for implementation and document the mapping. -->

## Dependencies

- Microsoft Agent Framework (Python): `agent-framework` package
- Ollama: Running locally with target model pulled
- PyYAML: For configuration loading
- Pydantic: For structured data models
