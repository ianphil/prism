# Specification: Foundation Agent Framework + Ollama Integration

## Overview

### Problem Statement

PRISM requires LLM-powered agents that can make social-media-style decisions (like, reply, reshare, scroll) given a feed of posts. Without a working agent infrastructure, none of the higher-level features (RAG feeds, simulation loops, experiments) can be built or tested.

### Solution Summary

Integrate Microsoft Agent Framework (Python) with Ollama to create a `SocialAgent` that accepts a text feed, reasons about it using a local LLM, and returns a structured decision (choice + reason + optional content). The system is config-driven, async-native, and provider-agnostic via the framework's `IChatClient` abstraction.

### Business Value

| Benefit | Impact |
|---------|--------|
| Local-first inference | No cloud API costs; full simulation runs on M3 Ultra |
| Provider flexibility | Swap Ollama/Azure/OpenAI without code changes |
| Structured decisions | Reliable, parseable agent outputs for downstream processing |
| Async foundation | Enables future parallelization of 250-500 agents |

## User Stories

### Researcher

**As a researcher**, I want to configure a simulation to use a specific LLM model (e.g., gpt-oss:20b or mistral) via a YAML file, so that I can control the quality/speed trade-off for my experiments.

**Acceptance Criteria:**
- A `configs/default.yaml` file specifies model name, endpoint, and inference parameters
- Changing `model_id` in the config switches the LLM without code changes
- The config is validated at startup with clear error messages for invalid values

### Developer

**As a developer**, I want a `SocialAgent` class that takes a feed of posts and returns a structured decision, so that I can build simulation loops on top of it.

**Acceptance Criteria:**
- `SocialAgent` accepts a profile (name, interests, personality traits) at construction
- `SocialAgent.decide(feed_text)` returns an `AgentDecision` with `choice`, `reason`, and optional `content`
- Valid choices are: `LIKE`, `REPLY`, `RESHARE`, `SCROLL`
- The decision is a Pydantic model, not raw text or dict

### Developer (Provider Swap)

**As a developer**, I want to swap between Ollama and other LLM providers without changing agent code, so that I can test with cloud models during development.

**Acceptance Criteria:**
- The LLM client is constructed from config, not hardcoded
- `OllamaChatClient` is the default; other clients can be injected
- Agent code depends on the `ChatAgent` abstraction, not a specific client

## Functional Requirements

### FR-1: LLM Client Configuration

| Requirement | Description |
|-------------|-------------|
| FR-1.1 | Load LLM configuration from YAML file (`configs/default.yaml`) |
| FR-1.2 | Configuration includes: `model_id`, `endpoint`, `temperature`, `max_tokens`, `seed` |
| FR-1.3 | Validate configuration at load time using Pydantic |
| FR-1.4 | Support environment variable overrides for `endpoint` and `model_id` |

### FR-2: Ollama Chat Client

| Requirement | Description |
|-------------|-------------|
| FR-2.1 | Create `OllamaChatClient` from validated configuration |
| FR-2.2 | Default endpoint: `http://localhost:11434` |
| FR-2.3 | Default model: `mistral` (for development) |
| FR-2.4 | Expose `create_agent()` for ChatAgent construction |

### FR-3: Social Agent

| Requirement | Description |
|-------------|-------------|
| FR-3.1 | `SocialAgent` wraps a `ChatAgent` with social-media decision-making behavior |
| FR-3.2 | Constructor accepts: `agent_id`, `name`, `interests` (list of strings), `personality` (str) |
| FR-3.3 | `decide(feed_text: str) -> AgentDecision` invokes the LLM and returns structured output |
| FR-3.4 | System prompt includes agent profile, decision constraints, and output format |
| FR-3.5 | Uses `response_format=AgentDecision` for structured output when supported |

### FR-4: Agent Decision Model

| Requirement | Description |
|-------------|-------------|
| FR-4.1 | `AgentDecision` is a Pydantic `BaseModel` |
| FR-4.2 | Fields: `choice` (Literal["LIKE", "REPLY", "RESHARE", "SCROLL"]), `reason` (str), `content` (str | None) |
| FR-4.3 | `content` is required when `choice` is `REPLY` or `RESHARE`, optional otherwise |
| FR-4.4 | `reason` explains the agent's reasoning in 1-3 sentences |

### FR-5: Prompt Templates

| Requirement | Description |
|-------------|-------------|
| FR-5.1 | System prompt template defines agent personality and decision-making behavior |
| FR-5.2 | User prompt template formats the feed for the agent |
| FR-5.3 | Templates use f-string interpolation with profile fields |
| FR-5.4 | Prompt constrains output to valid choices with examples |

## Non-Functional Requirements

### Performance

| Requirement | Target |
|-------------|--------|
| Single agent decision latency (mistral) | < 2 seconds |
| Single agent decision latency (gpt-oss:20b) | < 5 seconds |
| Config load time | < 100ms |

### Reliability

| Requirement | Target |
|-------------|--------|
| Graceful handling of Ollama server unavailable | Clear error message, no crash |
| Graceful handling of malformed LLM output | Fallback to SCROLL decision with error logged |
| Config validation errors | Raised at startup, not at runtime |

### Maintainability

| Requirement | Target |
|-------------|--------|
| Type annotations | All public functions and methods |
| Test coverage | >80% for new code |
| Code style | Passes ruff, flake8, black |

## Scope

### In Scope

- `OllamaChatClient` wrapper with config loading
- `SocialAgent` class with `decide()` method
- `AgentDecision` Pydantic model
- Prompt templates for social media decisions
- YAML configuration for model/endpoint/params
- Unit tests and one integration test (with mocked LLM)

### Out of Scope

- RAG feed retrieval (Feature 2)
- Simulation loop orchestration (Feature 3)
- Profile generation from real Twitter data (Feature 5)
- Multiple concurrent agents (Feature 3)
- OpenTelemetry tracing (Feature 6)
- CLI interface (Feature 7)

### Future Considerations

- Agent memory / conversation history across rounds
- Tool calling for RAG feed retrieval
- Batch inference for parallel agents
- Reasoning effort configuration (low/medium/high)

## Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Agent produces valid decision | 100% of test cases | Unit tests with mocked LLM |
| Config loads and validates | All valid configs accepted, invalid rejected | Config unit tests |
| Structured output works | `result.value` returns `AgentDecision` | Integration test |
| Provider swap works | Agent works with both Ollama and mock client | Dependency injection test |

## Assumptions

1. Microsoft Agent Framework Python beta (`1.0.0b260127`) is stable enough for development
2. `OllamaChatClient` supports `response_format` with Pydantic models for Ollama models that support structured output
3. Ollama is installed and running locally during integration tests
4. `mistral` model is available in Ollama for development/testing
5. `gpt-oss:20b` availability in Ollama is uncertain; config makes model swappable

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Agent Framework API changes in next beta | Medium | Medium | Pin version, wrap behind our interfaces |
| Structured output fails with Ollama models | Medium | High | Fall back to prompt-based JSON + manual parsing |
| `gpt-oss:20b` not in Ollama registry | High | Low | Use `mistral` for dev; model is config-driven |
| Ollama server flaky during tests | Low | Medium | Mock LLM client in unit tests; mark integration tests |

## Glossary

| Term | Definition |
|------|------------|
| ChatAgent | Microsoft Agent Framework class that wraps an LLM client with instructions and tools |
| IChatClient | Protocol/interface for LLM provider abstraction in Agent Framework |
| OllamaChatClient | Agent Framework's native Ollama integration class |
| AgentDecision | Pydantic model representing a social agent's choice + reason + content |
| SocialAgent | PRISM's wrapper around ChatAgent with social media decision behavior |
| Structured output | LLM response constrained to a specific schema (Pydantic model) |
