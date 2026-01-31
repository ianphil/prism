# Agent Behavior Statecharts Tasks (TDD)

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
| Researcher queries state distribution | FR-7 (State Query Methods) | agents_in_state counts agents, state_distribution returns counts |
| Experimenter traces state transitions | FR-5 (State History) | StateTransition records transitions, SocialAgent provides transition method |
| Developer prevents stuck agents | FR-6 (Timeout Transitions) | SocialAgent supports timeout detection |
| Debugger minimizes reasoner calls | FR-4 (LLM Reasoner Integration) | StatechartReasoner decides via LLM, Reasoner handles parse errors |

## Dependencies

```
Phase 1 (States + Transitions) ──► Phase 2 (Statechart Engine)
                                          │
                                          ├──► Phase 3 (Reasoner)
                                          │
                                          └──► Phase 4 (Timeouts)
                                                    │
                                                    ▼
                                          Phase 5 (Agent Integration)
                                                    │
                                                    ▼
                                          Phase 6 (Queries + Validation)
```

## Phase 1: Core Types

### AgentState Enum
- [x] T001 [TEST] Write tests for `AgentState` enum
  - All states are defined (IDLE, SCROLLING, EVALUATING, COMPOSING, ENGAGING_*, RESTING)
  - Inherits from str for JSON serialization
  - Values are lowercase strings
- [x] T002 [IMPL] Implement `AgentState` in `prism/statechart/states.py`

### Transition Dataclass
- [x] T003 [TEST] Write tests for `Transition` dataclass
  - Has trigger, source, target fields
  - Guard and action are optional (default None)
  - Is frozen (immutable)
- [x] T004 [IMPL] Implement `Transition` in `prism/statechart/transitions.py`

### StateTransition Record
- [x] T005 [TEST] Write tests for `StateTransition` dataclass
  - Has from_state, to_state, trigger, timestamp fields
  - Context is optional (default None)
  - Timestamp is datetime type
- [x] T006 [IMPL] Implement `StateTransition` in `prism/statechart/transitions.py`

## Phase 2: Statechart Engine

### Statechart Construction
- [x] T007 [TEST] Write tests for `Statechart.__init__()`
  - Accepts states (set), transitions (list), initial (AgentState)
  - Validates initial is in states
  - Validates all transition sources/targets are in states
  - Raises ValueError on invalid configuration
- [x] T008 [IMPL] Implement `Statechart.__init__()` in `prism/statechart/statechart.py`

### Transition Firing
- [x] T009 [TEST] Write tests for `Statechart.fire()`
  - Returns target state when transition matches
  - Returns None when no transition matches
  - Evaluates guards in definition order
  - First matching guard wins
- [x] T010 [IMPL] Implement `Statechart.fire()` basic logic

### Guard Fail-Safe
- [x] T011 [TEST] Write tests for guard exception handling
  - Guard that raises exception is treated as False
  - Guard that returns non-boolean is coerced to bool
  - Transition continues to next candidate on guard failure
- [x] T012 [IMPL] Implement guard fail-safe behavior

### Trigger Introspection
- [x] T013 [TEST] Write tests for `Statechart.valid_triggers()`
  - Returns list of triggers available from given state
  - Returns empty list for state with no outgoing transitions
- [x] T014 [TEST] Write tests for `Statechart.valid_targets()`
  - Returns list of possible target states for trigger from state
  - Returns empty list when no matching transitions
- [x] T015 [IMPL] Implement `valid_triggers()` and `valid_targets()`

## Phase 3: LLM Reasoner

### Reasoner Construction
- [x] T016 [TEST] Write tests for `StatechartReasoner.__init__()`
  - Accepts OllamaChatClient
  - Stores client reference
- [x] T017 [IMPL] Implement `StatechartReasoner.__init__()` in `prism/statechart/reasoner.py`

### Reasoner Prompt Building
- [x] T018 [TEST] Write tests for reasoner prompt construction
  - Includes agent name/interests in prompt
  - Includes current state and trigger
  - Includes available options with descriptions
  - Requests JSON response format
- [x] T019 [IMPL] Implement `build_reasoner_prompt()` function

### Reasoner Decision
- [x] T020 [TEST] Write tests for `StatechartReasoner.decide()` (async)
  - Returns AgentState from options
  - Calls LLM with constructed prompt
  - Parses JSON response correctly
- [x] T021 [IMPL] Implement `StatechartReasoner.decide()`

### Reasoner Error Handling
- [x] T022 [TEST] Write tests for reasoner parse error handling
  - JSON parse error returns fallback state
  - Invalid state in response returns fallback
  - Empty options raises ValueError
- [x] T023 [IMPL] Implement reasoner error handling

## Phase 4: Timeout Transitions

### Tick Tracking
- [x] T024 [TEST] Write tests for `SocialAgent.tick()`
  - Increments ticks_in_state by 1
  - Starts at 0 for new agents
- [x] T025 [IMPL] Add `tick()` method to `SocialAgent`

### Timeout Detection
- [x] T026 [TEST] Write tests for `SocialAgent.is_timed_out()`
  - Returns False when ticks_in_state <= timeout_threshold
  - Returns True when ticks_in_state > timeout_threshold
- [x] T027 [IMPL] Add `is_timed_out()` method to `SocialAgent`

### Timeout Threshold Configuration
- [x] T028 [TEST] Write tests for timeout_threshold parameter
  - Default value is 5
  - Can be set at construction
  - Must be > 0
- [x] T029 [IMPL] Add `timeout_threshold` parameter to `SocialAgent.__init__()`

## Phase 5: SocialAgent Integration

### State Field
- [x] T030 [TEST] Write tests for `SocialAgent.state` field
  - Default value is AgentState.IDLE
  - Can be set to any valid AgentState
- [x] T031 [IMPL] Add `state` field to `SocialAgent`

### State History
- [x] T032 [TEST] Write tests for `SocialAgent.state_history` field
  - Initialized as empty list
  - Contains StateTransition objects after transitions
- [x] T033 [IMPL] Add `state_history` field to `SocialAgent`

### Transition Method
- [x] T034 [TEST] Write tests for `SocialAgent.transition_to()`
  - Updates state to new value
  - Appends StateTransition to history
  - Resets ticks_in_state to 0
  - No-op for self-transitions (same state)
- [x] T035 [IMPL] Implement `transition_to()` method

### History Depth Limiting
- [x] T036 [TEST] Write tests for history pruning
  - History does not exceed max_history_depth
  - Oldest entries removed first (FIFO)
- [x] T037 [IMPL] Implement history pruning in `transition_to()`

### Engagement Threshold
- [x] T038 [TEST] Write tests for `engagement_threshold` parameter
  - Default value is 0.5
  - Can be set at construction
  - Used by `should_engage()` guard helper
- [x] T039 [IMPL] Add `engagement_threshold` and `should_engage()` to `SocialAgent`

## Phase 6: State Queries and Validation

### Query Functions
- [ ] T040 [TEST] Write tests for `agents_in_state()`
  - Returns count of agents in given state
  - Returns 0 for empty list
  - Returns 0 when no agents in state
- [ ] T041 [IMPL] Implement `agents_in_state()` in `prism/statechart/queries.py`

- [ ] T042 [TEST] Write tests for `state_distribution()`
  - Returns dict mapping each AgentState to count
  - All states present in result (even with 0 count)
  - Correct counts for mixed agent states
- [ ] T043 [IMPL] Implement `state_distribution()`

### Package Exports
- [ ] T044 [IMPL] Create `prism/statechart/__init__.py` with exports
  - AgentState, Transition, StateTransition
  - Statechart, StatechartReasoner
  - agents_in_state, state_distribution
- [ ] T045 [IMPL] Create `tests/statechart/__init__.py`

### Integration Test
- [ ] T046 [TEST] Write integration test
  - Create statechart with social agent states
  - Create agent and fire transitions
  - Verify state changes and history recording
  - Test timeout detection and recovery
  - Test reasoner invocation for ambiguous case (mock LLM)

### Spec Tests
- [ ] T047 [SPEC] Run spec tests using `specs/tests/003-agent-behavior-statecharts.md`
  - All tests pass with opencode or codex runner

## Task Summary

| Phase | Tasks | [TEST] | [IMPL] | [SPEC] |
|-------|-------|--------|--------|--------|
| Phase 1: Core Types | T001-T006 | 3 | 3 | 0 |
| Phase 2: Statechart Engine | T007-T015 | 5 | 4 | 0 |
| Phase 3: LLM Reasoner | T016-T023 | 4 | 4 | 0 |
| Phase 4: Timeout | T024-T029 | 3 | 3 | 0 |
| Phase 5: Agent Integration | T030-T039 | 5 | 5 | 0 |
| Phase 6: Queries + Validation | T040-T047 | 3 | 4 | 1 |
| **Total** | **47** | **23** | **23** | **1** |

## Final Validation

After all implementation phases are complete:

- [ ] `uv run ruff check .` passes
- [ ] `uv run flake8 .` passes
- [ ] `uv run black --check .` passes
- [ ] `uv run pytest` passes (all tests including new statechart tests)
- [ ] Run spec tests with `/spec-tests` skill using `specs/tests/003-agent-behavior-statecharts.md`
- [ ] All spec tests pass → feature complete
