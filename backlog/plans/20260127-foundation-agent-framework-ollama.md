---
title: "Foundation: Agent Framework + Ollama Integration"
status: open
priority: high
created: 2026-01-27
---

# Foundation: Agent Framework + Ollama Integration

## Summary

Establish the core infrastructure by integrating Microsoft Agent Framework with Ollama, creating a working `ChatAgent` that can make decisions using gpt-oss:20b.

## Motivation

This is the foundational layer for PRISM. All other features (RAG, simulation loop, experiments) depend on having working LLM-powered agents. Without this, nothing else can proceed.

## Proposal

### Goals

- Install and configure Microsoft Agent Framework (Python)
- Integrate Ollama as the primary LLM provider via `IChatClient`
- Create a basic `SocialAgent` class wrapping `ChatAgent`
- Validate agent decision-making with gpt-oss:20b
- Support fallback to Mistral 7B for faster development iteration

### Non-Goals

- RAG/feed retrieval (Feature 2)
- Full simulation orchestration (Feature 3)
- Profile generation from real Twitter data (Feature 5)

## Design

The foundation follows the PRD's proposed structure:

1. **LLM Client Layer**: Implement `OllamaChatClient` conforming to `IChatClient` abstraction, supporting both gpt-oss:20b and Mistral 7B via config
2. **Agent Layer**: `SocialAgent` wraps `ChatAgent` with social-media-specific prompt templates and structured output (Choice-Reason-Content triplets)
3. **Configuration**: YAML-driven config for model selection, Ollama endpoint, reasoning effort level
4. **Validation**: Simple test harness to verify agent produces valid decisions given a mock feed

## Tasks

- [ ] Set up project structure per PRD Appendix D (`prism/` package skeleton)
- [ ] Install Agent Framework: `pip install agent-framework --pre`
- [ ] Implement `OllamaChatClient` with `IChatClient` interface
- [ ] Create `SocialAgent` class with decision prompt template
- [ ] Define `AgentDecision` dataclass (choice, reason, content)
- [ ] Add YAML config for model/endpoint settings (`configs/default.yaml`)
- [ ] Write integration test: agent makes valid decision from mock feed

## Open Questions

- Is `agent-framework` the correct package name, or has it changed in preview?
- Does gpt-oss:20b exist in Ollama registry, or is this a placeholder model name?
