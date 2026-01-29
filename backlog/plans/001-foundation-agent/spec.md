# Specification: Foundation Agent Framework + Ollama Integration

## Overview

### Problem Statement

PRISM requires LLM-powered agents that can make realistic social media decisions. Without a foundational agent framework integrated with local LLM inference, no other features (RAG, simulation, experiments) can proceed. Currently, the codebase has no agent infrastructure.

### Solution Summary

Integrate Microsoft Agent Framework with Ollama to create a working `SocialAgent` class that wraps `ChatAgent` and produces structured decisions (Choice-Reason-Content triplets) using local LLM inference.

### Business Value

| Benefit | Impact |
|---------|--------|
| Enables all downstream features | RAG, simulation, experiments depend on this |
| Local-first inference | No cloud API costs for development |
| Quality agent reasoning | gpt-oss:20b provides human-like decisions |
| Provider flexibility | IChatClient abstraction allows swapping LLMs |

## User Stories

### Researcher

**As a researcher**, I want agents to make realistic social media decisions, so that simulation results reflect human behavior patterns.

**Acceptance Criteria:**
- Agent produces structured decisions (choice, reason, content)
- Decisions include IGNORE, LIKE, REPLY, or RESHARE
- Generated content (for REPLY/RESHARE) reads naturally

### Developer

**As a developer**, I want to configure the LLM provider via YAML, so that I can switch between models without code changes.

**Acceptance Criteria:**
- YAML config specifies model, endpoint, and reasoning effort
- Changing config file changes model behavior
- Both gpt-oss:20b and Mistral 7B supported

### System

**As the system**, I want a standardized agent interface, so that the simulation loop can orchestrate many agents uniformly.

**Acceptance Criteria:**
- `SocialAgent` exposes `decide(feed)` method
- Returns `AgentDecision` dataclass
- Works with any IChatClient implementation

## Functional Requirements

### FR-1: LLM Client Layer

| Requirement | Description |
|-------------|-------------|
| FR-1.1 | Implement `OllamaChatClient` conforming to `IChatClient` interface |
| FR-1.2 | Support configurable endpoint URL (default: localhost:11434) |
| FR-1.3 | Support configurable model name (default: gpt-oss:20b) |
| FR-1.4 | Support reasoning effort parameter (low/medium/high) |

### FR-2: Agent Layer

| Requirement | Description |
|-------------|-------------|
| FR-2.1 | Create `SocialAgent` class wrapping `ChatAgent` |
| FR-2.2 | Accept agent profile (name, interests, personality) at construction |
| FR-2.3 | Implement `decide(feed: list[Post]) -> AgentDecision` method |
| FR-2.4 | Support all decision types: IGNORE, LIKE, REPLY, RESHARE |

### FR-3: Structured Output

| Requirement | Description |
|-------------|-------------|
| FR-3.1 | Define `AgentDecision` dataclass with choice, reason, content fields |
| FR-3.2 | `choice` is enum: IGNORE, LIKE, REPLY, RESHARE |
| FR-3.3 | `reason` explains decision rationale (1-2 sentences) |
| FR-3.4 | `content` contains generated text for REPLY/RESHARE (None for IGNORE/LIKE) |

### FR-4: Configuration

| Requirement | Description |
|-------------|-------------|
| FR-4.1 | Load configuration from YAML file |
| FR-4.2 | Support environment variable overrides |
| FR-4.3 | Validate configuration on load |
| FR-4.4 | Provide sensible defaults |

## Non-Functional Requirements

### Performance

| Requirement | Target |
|-------------|--------|
| Single decision latency | <5s with gpt-oss:20b |
| Memory per agent | <100MB |
| Startup time | <2s to first decision |

### Reliability

| Requirement | Target |
|-------------|--------|
| LLM timeout handling | Retry once, then fail gracefully |
| Invalid response handling | Parse best-effort, log warnings |
| Configuration validation | Fail fast on invalid config |

### Maintainability

| Requirement | Target |
|-------------|--------|
| Test coverage | >80% for core modules |
| Type annotations | All public interfaces |
| Documentation | Docstrings for public API |

## Scope

### In Scope

- OllamaChatClient implementation
- SocialAgent class with decide() method
- AgentDecision dataclass
- YAML configuration loading
- Integration test with mock feed
- Prompt templates for social decisions

### Out of Scope

- RAG/feed retrieval (Feature 002)
- Full simulation orchestration (Feature 003)
- Profile generation from real data (Feature 004)
- Multiple LLM provider implementations (future)

### Future Considerations

- Azure OpenAI client implementation
- OpenAI API client implementation
- Agent memory/context persistence
- Batch inference optimization

## Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Agent produces valid decision | 100% | All decisions parse to AgentDecision |
| Decision quality | Subjective review | Decisions are contextually appropriate |
| Config flexibility | 2+ models | Switch between models via config |
| Test coverage | >80% | pytest --cov report |

## Assumptions

1. Microsoft Agent Framework Python package is available and stable enough for use
2. Ollama is running locally with required model pulled
3. Target model (gpt-oss:20b or equivalent) produces coherent social media content
4. Single-agent decisions complete in <5s on M3 Ultra

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Agent Framework API changes | Medium | High | Pin version, maintain abstraction |
| Model not available in Ollama | Low | High | Use alternative (llama3, mistral) |
| Response parsing failures | Medium | Medium | Robust parsing with fallbacks |
| Inference too slow | Low | Medium | Use faster model for development |

## Glossary

| Term | Definition |
|------|------------|
| IChatClient | Agent Framework interface for LLM providers |
| ChatAgent | Agent Framework base class for conversational agents |
| SocialAgent | Our wrapper adding social media decision behavior |
| AgentDecision | Structured output: choice + reason + content |
| gpt-oss:20b | Hypothetical OpenAI open-weight model from PRD |
