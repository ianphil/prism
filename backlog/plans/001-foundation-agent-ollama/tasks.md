# Foundation Agent Framework + Ollama — Tasks (TDD)

## TDD Approach

All implementation follows strict Red-Green-Refactor:
1. **RED**: Write failing test first
2. **GREEN**: Write minimal code to pass test
3. **REFACTOR**: Clean up while keeping tests green

### Two Test Layers

| Layer | Purpose | When to Run |
|-------|---------|-------------|
| **Unit Tests** | Implementation TDD (Red-Green-Refactor) | During implementation |
| **Spec Tests** | Intent-based acceptance validation | After all phases complete |

## User Story Mapping

| Story | spec.md Reference | Spec Tests |
|-------|-------------------|------------|
| Researcher configures LLM via YAML | FR-1 (LLM Client Configuration) | LLMConfig validated, Config loads from YAML, Default YAML exists |
| Developer uses SocialAgent.decide() | FR-3 (Social Agent), FR-4 (Decision Model) | AgentDecision model, SocialAgent wraps ChatAgent |
| Developer swaps LLM providers | FR-2 (Ollama Chat Client) | Client factory creates OllamaChatClient |

## Dependencies

```
Phase 1 (Models + Config) ──► Phase 2 (LLM Client) ──► Phase 3 (Agent Layer)
                                                              │
                                                              ▼
                                                       Phase 4 (Integration)
```

## Phase 1: Data Models and Configuration

### AgentDecision Model
- [x] T001 [TEST] Write tests for `AgentDecision` Pydantic model
  - Valid decision with all fields
  - LIKE/SCROLL with `content=None` is valid
  - REPLY without content raises validation error
  - RESHARE without content raises validation error
  - Invalid choice value raises validation error
  - Empty reason raises validation error
- [x] T002 [IMPL] Implement `AgentDecision` in `prism/agents/decision.py`
  - Pydantic BaseModel with choice/reason/content
  - field_validator for content requirement

### Configuration
- [x] T003 [TEST] Write tests for `LLMConfig` Pydantic model
  - Default values are correct
  - Valid config parses successfully
  - Temperature out of range raises error
  - max_tokens <= 0 raises error
- [x] T004 [IMPL] Implement `LLMConfig` and `PrismConfig` in `prism/llm/config.py`
- [x] T005 [TEST] Write tests for `load_config()`
  - Loads valid YAML file
  - Returns PrismConfig with LLMConfig populated
  - Missing file raises FileNotFoundError
  - Invalid YAML raises appropriate error
- [x] T006 [IMPL] Implement `load_config()` in `prism/llm/config.py`
- [x] T007 [IMPL] Create `configs/default.yaml` with default values

## Phase 2: LLM Client

### Client Factory
- [ ] T008 [TEST] Write tests for `create_llm_client()`
  - Creates OllamaChatClient with config values
  - Passes host and model_id correctly
- [ ] T009 [IMPL] Implement `create_llm_client()` in `prism/llm/client.py`

## Phase 3: Agent Layer

### Prompt Templates
- [ ] T010 [TEST] Write tests for prompt template functions
  - System prompt includes agent interests and personality
  - System prompt mentions valid choices (LIKE, REPLY, RESHARE, SCROLL)
  - Feed prompt formats input text
- [ ] T011 [IMPL] Implement prompt templates in `prism/agents/prompts.py`
  - `build_system_prompt(name, interests, personality)` → str
  - `build_feed_prompt(feed_text)` → str

### SocialAgent
- [ ] T012 [TEST] Write tests for `SocialAgent`
  - Construction with profile data
  - `decide()` returns AgentDecision from mocked ChatAgent
  - Fallback parsing when structured output is None
  - Default SCROLL on parse failure
- [ ] T013 [IMPL] Implement `SocialAgent` in `prism/agents/social_agent.py`
  - Constructor: agent_id, name, interests, personality, chat_agent
  - `async decide(feed_text)` → AgentDecision
  - Structured output with fallback

### Package Exports
- [ ] T014 [IMPL] Create `__init__.py` files with exports
  - `prism/llm/__init__.py`
  - `prism/agents/__init__.py`
  - `tests/llm/__init__.py`
  - `tests/agents/__init__.py`

## Phase 4: Integration Validation

- [x] T015 [IMPL] Add runtime dependencies via `uv add`
  - `uv add agent-framework-ollama --pre`
  - `uv add pydantic`
  - `uv add pyyaml`
- [ ] T016 [SPEC] Run spec tests using `specs/tests/001-foundation-agent-ollama.md`
- [ ] T017 [TEST] Write integration test (marked with `@pytest.mark.integration`)
  - Requires running Ollama with `mistral` model
  - Creates SocialAgent from config
  - Calls `decide()` with sample feed text
  - Validates returned AgentDecision has valid choice

## Task Summary

| Phase | Tasks | [TEST] | [IMPL] | [SPEC] |
|-------|-------|--------|--------|--------|
| Phase 1: Models + Config | T001-T007 | 3 | 4 | 0 |
| Phase 2: LLM Client | T008-T009 | 1 | 1 | 0 |
| Phase 3: Agent Layer | T010-T014 | 2 | 3 | 0 |
| Phase 4: Integration | T015-T017 | 1 | 1 | 1 |
| **Total** | **17** | **7** | **9** | **1** |

## Final Validation

After all implementation phases are complete:

- [ ] `uv run ruff check .` passes
- [ ] `uv run flake8 .` passes
- [ ] `uv run black --check .` passes
- [ ] `uv run pytest` passes
- [ ] Run spec tests with `/spec-tests` skill using `specs/tests/001-foundation-agent-ollama.md`
- [ ] All spec tests pass → feature complete
