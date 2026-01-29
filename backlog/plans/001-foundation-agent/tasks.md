# Foundation Agent Framework Tasks (TDD)

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
| Researcher: realistic decisions | FR-2, FR-3 | Decision Structure, Valid Output |
| Developer: YAML config | FR-4 | Configuration Loading |
| System: standardized interface | FR-1, FR-2 | Client Interface, Agent Interface |

## Dependencies

```
Phase 1 ──► Phase 2 ──► Phase 4 ──► Phase 5
              │
              ▼
           Phase 3
```

- Phase 1: No dependencies (core data models)
- Phase 2: Depends on Phase 1 (LLM client uses models)
- Phase 3: Depends on Phase 1 (config uses models)
- Phase 4: Depends on Phases 2, 3 (agent uses client + config)
- Phase 5: Depends on Phase 4 (integration tests agent)

## Phase 1: Core Data Models

### Data Structures

- [ ] T001 [TEST] Write test for Choice enum values
- [ ] T002 [IMPL] Implement Choice enum with IGNORE, LIKE, REPLY, RESHARE
- [ ] T003 [TEST] Write test for AgentDecision dataclass fields
- [ ] T004 [IMPL] Implement AgentDecision dataclass
- [ ] T005 [TEST] Write test for AgentDecision validation (content matches choice)
- [ ] T006 [IMPL] Add validation to AgentDecision
- [ ] T007 [TEST] Write test for AgentProfile dataclass fields
- [ ] T008 [IMPL] Implement AgentProfile dataclass
- [ ] T009 [TEST] Write test for Post dataclass fields
- [ ] T010 [IMPL] Implement Post dataclass with media fields

### Phase 1 Exit

- [ ] T011 [SPEC] Run spec tests for Phase 1 → expect pass for data model tests

## Phase 2: LLM Client

### Ollama Client

- [ ] T012 [TEST] Write test for OllamaChatClient initialization
- [ ] T013 [IMPL] Implement OllamaChatClient.__init__ with endpoint/model
- [ ] T014 [TEST] Write test for OllamaChatClient.chat() with mocked response
- [ ] T015 [IMPL] Implement OllamaChatClient.chat() using httpx
- [ ] T016 [TEST] Write test for timeout handling
- [ ] T017 [IMPL] Add timeout handling to chat()
- [ ] T018 [TEST] Write test for error response handling
- [ ] T019 [IMPL] Add error handling for non-200 responses

### Phase 2 Exit

- [ ] T020 [SPEC] Run spec tests for Phase 2 → expect pass for LLM client tests

## Phase 3: Configuration

### Config Loading

- [ ] T021 [TEST] Write test for LLMConfig dataclass validation
- [ ] T022 [IMPL] Implement LLMConfig with Pydantic validation
- [ ] T023 [TEST] Write test for loading config from YAML file
- [ ] T024 [IMPL] Implement load_config() function
- [ ] T025 [TEST] Write test for environment variable overrides
- [ ] T026 [IMPL] Add env var override support
- [ ] T027 [TEST] Write test for default config values
- [ ] T028 [IMPL] Implement default configuration

### Config File

- [ ] T029 [IMPL] Create configs/default.yaml with documented settings

### Phase 3 Exit

- [ ] T030 [SPEC] Run spec tests for Phase 3 → expect pass for config tests

## Phase 4: Agent Implementation

### Prompts

- [ ] T031 [TEST] Write test for system prompt generation from profile
- [ ] T032 [IMPL] Implement build_system_prompt(profile) function
- [ ] T033 [TEST] Write test for user prompt generation from feed
- [ ] T034 [IMPL] Implement build_user_prompt(feed) function
- [ ] T035 [TEST] Write test for decision response parsing
- [ ] T036 [IMPL] Implement parse_decision_response() function

### SocialAgent

- [ ] T037 [TEST] Write test for SocialAgent initialization
- [ ] T038 [IMPL] Implement SocialAgent.__init__ with profile and client
- [ ] T039 [TEST] Write test for SocialAgent.decide() with mocked client
- [ ] T040 [IMPL] Implement SocialAgent.decide() method
- [ ] T041 [TEST] Write test for invalid response handling in decide()
- [ ] T042 [IMPL] Add fallback behavior for unparseable responses

### Phase 4 Exit

- [ ] T043 [SPEC] Run spec tests for Phase 4 → expect pass for agent tests

## Phase 5: Integration

### End-to-End Test

- [ ] T044 [TEST] Write integration test: agent decides on mock feed
- [ ] T045 [IMPL] Ensure all components work together
- [ ] T046 [TEST] Write test for config-driven model selection
- [ ] T047 [IMPL] Verify model can be changed via config

### Documentation

- [ ] T048 [IMPL] Add docstrings to all public classes/methods
- [ ] T049 [IMPL] Update prism/__init__.py with exports

### Cleanup

- [ ] T050 [IMPL] Run ruff format and fix any issues
- [ ] T051 [IMPL] Run flake8 and fix any issues

### Phase 5 Exit

- [ ] T052 [SPEC] Run ALL spec tests → expect ALL PASS

## Task Summary

| Phase | Tasks | [TEST] | [IMPL] | [SPEC] |
|-------|-------|--------|--------|--------|
| Phase 1: Data Models | T001-T011 | 5 | 5 | 1 |
| Phase 2: LLM Client | T012-T020 | 4 | 4 | 1 |
| Phase 3: Configuration | T021-T030 | 4 | 5 | 1 |
| Phase 4: Agent | T031-T043 | 6 | 6 | 1 |
| Phase 5: Integration | T044-T052 | 2 | 5 | 1 |
| **Total** | **52** | **21** | **25** | **5** |

## Final Validation

After all implementation phases are complete:

- [ ] `uv run pytest` passes
- [ ] `uv run ruff check .` passes
- [ ] `uv run flake8 .` passes
- [ ] `uv run black --check .` passes
- [ ] Run spec tests with `specs/tests/001-foundation-agent.md`
- [ ] All spec tests pass → feature complete

## Quick Reference

```bash
# Run tests
uv run pytest tests/

# Run specific test file
uv run pytest tests/agents/test_decisions.py

# Run with coverage
uv run pytest --cov=prism tests/

# Lint
uv run ruff check .
uv run flake8 .

# Format
uv run ruff format .
uv run black .
```
