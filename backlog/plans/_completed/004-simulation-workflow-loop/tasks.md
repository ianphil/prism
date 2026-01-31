# Simulation Workflow Loop Tasks (TDD)

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
| US-1: Run Basic Simulation | FR-4: Round Controller | Controller Iterates Rounds, Returns Final Result |
| US-2: Resume From Checkpoint | FR-5: Checkpointing | Checkpointer Saves/Loads State |
| US-3: Understand Decisions | FR-3: Decision Flow | Decision Executor Uses Statechart |
| US-4: State Distribution | FR-1: State Management | State Distribution Available |

## Dependencies

```
Phase 1 (State Foundation)
    │
    ▼
Phase 2 (Triggers & Factory)
    │
    ├───────────────────┐
    ▼                   ▼
Phase 3 (Executors)  Phase 4 (Controller & Checkpoint)
    │                   │
    └─────────┬─────────┘
              ▼
        Phase 5 (Integration)
```

---

## Phase 1: State Foundation

Core data models for simulation state management.

### Configuration

- [x] T001 [TEST] Write test for SimulationConfig with default values
- [x] T002 [IMPL] Implement SimulationConfig Pydantic model with defaults
- [x] T003 [TEST] Write test for SimulationConfig validation (max_rounds >= 1)
- [x] T004 [IMPL] Implement validation for max_rounds and checkpoint_frequency
- [x] T005 [TEST] Write test for Path field parsing from strings
- [x] T006 [IMPL] Implement Path field validator

### Engagement Metrics

- [x] T007 [TEST] Write test for EngagementMetrics with default zero values
- [x] T008 [IMPL] Implement EngagementMetrics dataclass
- [x] T009 [TEST] Write test for EngagementMetrics increment methods
- [x] T010 [IMPL] Implement increment_like, increment_reshare, etc.

### Simulation State

- [x] T011 [TEST] Write test for SimulationState with required fields
- [x] T012 [IMPL] Implement SimulationState with posts, agents, statechart
- [x] T013 [TEST] Write test for SimulationState validates non-empty agents
- [x] T014 [IMPL] Implement agent list validation
- [x] T015 [TEST] Write test for get_state_distribution returns dict
- [x] T016 [IMPL] Implement get_state_distribution delegating to queries
- [x] T017 [TEST] Write test for add_post adds to posts and increments metrics
- [x] T018 [IMPL] Implement add_post method
- [x] T019 [TEST] Write test for advance_round increments round_number
- [x] T020 [IMPL] Implement advance_round method

### Result Types

- [x] T021 [TEST] Write test for ActionResult dataclass
- [x] T022 [IMPL] Implement ActionResult
- [x] T023 [TEST] Write test for DecisionResult dataclass
- [x] T024 [IMPL] Implement DecisionResult
- [x] T025 [TEST] Write test for RoundResult dataclass
- [x] T026 [IMPL] Implement RoundResult
- [x] T027 [TEST] Write test for SimulationResult dataclass
- [x] T028 [IMPL] Implement SimulationResult

---

## Phase 2: Triggers & Statechart Factory

Trigger determination and default statechart definition.

### Trigger Determination

- [x] T029 [TEST] Write test for determine_trigger returns string
- [x] T030 [IMPL] Implement determine_trigger function signature
- [x] T031 [TEST] Write test for IDLE → "start_browsing"
- [x] T032 [IMPL] Implement IDLE trigger case
- [x] T033 [TEST] Write test for SCROLLING + feed → "sees_post"
- [x] T034 [IMPL] Implement SCROLLING with feed trigger case
- [x] T035 [TEST] Write test for SCROLLING + empty feed → "feed_empty"
- [x] T036 [IMPL] Implement SCROLLING without feed trigger case
- [x] T037 [TEST] Write test for EVALUATING → "decides"
- [x] T038 [IMPL] Implement EVALUATING trigger case
- [x] T039 [TEST] Write test for COMPOSING → "finishes_composing"
- [x] T040 [IMPL] Implement COMPOSING trigger case
- [x] T041 [TEST] Write test for ENGAGING_* → "finishes_engaging"
- [x] T042 [IMPL] Implement ENGAGING states trigger case
- [x] T043 [TEST] Write test for RESTING → "rested"
- [x] T044 [IMPL] Implement RESTING trigger case

### Statechart Factory

- [x] T045 [TEST] Write test for create_social_media_statechart returns Statechart
- [x] T046 [IMPL] Implement factory function signature
- [x] T047 [TEST] Write test for statechart has all AgentState values
- [x] T048 [IMPL] Add all states to statechart
- [x] T049 [TEST] Write test for statechart has initial state IDLE
- [x] T050 [IMPL] Set initial state to IDLE
- [x] T051 [TEST] Write test for transition IDLE → SCROLLING on "start_browsing"
- [x] T052 [IMPL] Add start_browsing transition
- [x] T053 [TEST] Write test for transition SCROLLING → EVALUATING on "sees_post"
- [x] T054 [IMPL] Add sees_post transition
- [x] T055 [TEST] Write test for transition SCROLLING → RESTING on "feed_empty"
- [x] T056 [IMPL] Add feed_empty transition
- [x] T057 [TEST] Write test for transitions from EVALUATING on "decides"
- [x] T058 [IMPL] Add decides transitions to COMPOSING, ENGAGING_*, SCROLLING
- [x] T059 [TEST] Write test for finishing transitions back to SCROLLING
- [x] T060 [IMPL] Add finishes_composing and finishes_engaging transitions
- [x] T061 [TEST] Write test for timeout transition from any state
- [x] T062 [IMPL] Add timeout transitions

---

## Phase 3: Executors

Pipeline executors for agent rounds.

### Feed Retrieval Executor

- [x] T063 [TEST] Write test for FeedRetrievalExecutor.execute returns list[Post]
- [x] T064 [IMPL] Implement FeedRetrievalExecutor.execute
- [x] T065 [TEST] Write test for executor uses agent.interests for retrieval
- [x] T066 [IMPL] Wire up FeedRetriever.get_feed with agent interests

### Decision Executor

- [x] T067 [TEST] Write test for AgentDecisionExecutor.execute calls agent.tick
- [x] T068 [IMPL] Implement tick call at start of execute
- [x] T069 [TEST] Write test for execute calls statechart.fire with correct args
- [x] T070 [IMPL] Implement statechart.fire call
- [x] T071 [TEST] Write test for execute detects multiple valid targets
- [x] T072 [IMPL] Implement valid_targets check for ambiguous case
- [x] T073 [TEST] Write test for execute calls reasoner.decide when ambiguous
- [x] T074 [IMPL] Implement reasoner invocation
- [x] T075 [TEST] Write test for execute calls agent.transition_to
- [x] T076 [IMPL] Implement transition_to call
- [x] T077 [TEST] Write test for execute returns DecisionResult
- [x] T078 [IMPL] Implement DecisionResult construction and return
- [x] T079 [TEST] Write test for action execution based on new state
- [x] T080 [IMPL] Implement _execute_action method

### State Update Executor

- [x] T081 [TEST] Write test for StateUpdateExecutor handles like action
- [x] T082 [IMPL] Implement like handling (increment post.likes and metrics)
- [x] T083 [TEST] Write test for executor handles reply action
- [x] T084 [IMPL] Implement reply handling (increment + add post)
- [x] T085 [TEST] Write test for executor handles reshare action
- [x] T086 [IMPL] Implement reshare handling
- [x] T087 [TEST] Write test for executor handles compose action
- [x] T088 [IMPL] Implement compose handling (add new post)
- [x] T089 [TEST] Write test for executor handles scroll action (no changes)
- [x] T090 [IMPL] Implement scroll handling (no-op)

### Logging Executor

- [x] T091 [TEST] Write test for LoggingExecutor.execute logs JSON entry
- [x] T092 [IMPL] Implement structured JSON logging
- [x] T093 [TEST] Write test for log entry contains required fields
- [x] T094 [IMPL] Include timestamp, round, agent_id, trigger, states, action
- [x] T095 [TEST] Write test for executor writes to file when configured
- [x] T096 [IMPL] Implement file writing with flush

### Agent Round Executor

- [x] T097 [TEST] Write test for AgentRoundExecutor coordinates pipeline
- [x] T098 [IMPL] Implement AgentRoundExecutor.execute calling all executors
- [x] T099 [TEST] Write test for executor returns DecisionResult
- [x] T100 [IMPL] Wire up return value from decision executor

---

## Phase 4: Controller & Checkpoint

Round orchestration and state persistence.

### Checkpointer

- [x] T101 [TEST] Write test for Checkpointer.save creates JSON file
- [x] T102 [IMPL] Implement save method with JSON serialization
- [x] T103 [TEST] Write test for saved file includes version field
- [x] T104 [IMPL] Add version to CheckpointData
- [x] T105 [TEST] Write test for file path includes round number
- [x] T106 [IMPL] Implement filename pattern checkpoint_round_NNNN.json
- [x] T107 [TEST] Write test for atomic write (temp file + rename)
- [x] T108 [IMPL] Implement temp file pattern
- [x] T109 [TEST] Write test for Checkpointer.load reconstructs state
- [x] T110 [IMPL] Implement load method
- [x] T111 [TEST] Write test for load validates version
- [x] T112 [IMPL] Implement version check with ValueError
- [x] T113 [TEST] Write test for latest_checkpoint finds most recent
- [x] T114 [IMPL] Implement latest_checkpoint method
- [x] T115 [TEST] Write test for checkpoint_for_round finds specific round
- [x] T116 [IMPL] Implement checkpoint_for_round method

### Round Controller

- [x] T117 [TEST] Write test for RoundController.run_simulation iterates rounds
- [x] T118 [IMPL] Implement round iteration loop
- [x] T119 [TEST] Write test for controller processes all agents each round
- [x] T120 [IMPL] Implement agent iteration within round
- [x] T121 [TEST] Write test for controller saves checkpoints at frequency
- [x] T122 [IMPL] Implement checkpoint saving with frequency check
- [x] T123 [TEST] Write test for controller skips checkpoints when dir is None
- [x] T124 [IMPL] Implement checkpoint skip logic
- [x] T125 [TEST] Write test for controller advances round_number
- [x] T126 [IMPL] Implement state.advance_round call
- [x] T127 [TEST] Write test for controller returns SimulationResult
- [x] T128 [IMPL] Implement result construction
- [x] T129 [TEST] Write test for run_round executes single round
- [x] T130 [IMPL] Implement run_round method
- [x] T131 [TEST] Write test for resume_from_checkpoint loads and continues
- [x] T132 [IMPL] Implement resume_from_checkpoint method

---

## Phase 5: Integration

End-to-end integration and entry point.

### Config Integration

- [x] T133 [TEST] Write test for configs/default.yaml has simulation section
- [x] T134 [IMPL] Add simulation section to default.yaml
- [x] T135 [TEST] Write test for load_config reads simulation section
- [x] T136 [IMPL] Implement config loading function

### Module Exports

- [x] T137 [TEST] Write test for prism/simulation/__init__.py exports
- [x] T138 [IMPL] Create __init__.py with public exports
- [x] T139 [TEST] Write test for prism/simulation/executors/__init__.py exports
- [x] T140 [IMPL] Create executors/__init__.py

### Integration Test

- [x] T141 [TEST] Write integration test: 3 agents × 2 rounds completes
- [x] T142 [IMPL] Wire up all components in controller
- [x] T143 [TEST] Write integration test: checkpoint/resume produces same state
- [x] T144 [IMPL] Verify checkpoint serialization round-trips correctly
- [x] T145 [TEST] Write integration test: state distribution logged each round
- [x] T146 [IMPL] Verify logging executor output

### Entry Point

- [x] T147 [TEST] Write test for main.py has run_simulation function
- [x] T148 [IMPL] Add run_simulation to main.py
- [x] T149 [SPEC] Run spec tests for 004-simulation-workflow-loop

---

## Task Summary

| Phase | Tasks | [TEST] | [IMPL] | [SPEC] |
|-------|-------|--------|--------|--------|
| Phase 1: State Foundation | T001-T028 | 14 | 14 | 0 |
| Phase 2: Triggers & Factory | T029-T062 | 17 | 17 | 0 |
| Phase 3: Executors | T063-T100 | 19 | 19 | 0 |
| Phase 4: Controller & Checkpoint | T101-T132 | 16 | 16 | 0 |
| Phase 5: Integration | T133-T149 | 8 | 8 | 1 |
| **Total** | **149** | **74** | **74** | **1** |

---

## Final Validation

After all implementation phases are complete:

- [x] `uv run ruff check .` passes
- [x] `uv run ruff format --check .` passes
- [x] `uv run pytest tests/simulation/` passes (187 tests)
- [x] Run spec tests with `/spec-tests` skill using `specs/tests/004-simulation-workflow-loop.md`
- [x] All spec tests pass (21/21) → feature complete
