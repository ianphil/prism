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

- [ ] T001 [TEST] Write test for SimulationConfig with default values
- [ ] T002 [IMPL] Implement SimulationConfig Pydantic model with defaults
- [ ] T003 [TEST] Write test for SimulationConfig validation (max_rounds >= 1)
- [ ] T004 [IMPL] Implement validation for max_rounds and checkpoint_frequency
- [ ] T005 [TEST] Write test for Path field parsing from strings
- [ ] T006 [IMPL] Implement Path field validator

### Engagement Metrics

- [ ] T007 [TEST] Write test for EngagementMetrics with default zero values
- [ ] T008 [IMPL] Implement EngagementMetrics dataclass
- [ ] T009 [TEST] Write test for EngagementMetrics increment methods
- [ ] T010 [IMPL] Implement increment_like, increment_reshare, etc.

### Simulation State

- [ ] T011 [TEST] Write test for SimulationState with required fields
- [ ] T012 [IMPL] Implement SimulationState with posts, agents, statechart
- [ ] T013 [TEST] Write test for SimulationState validates non-empty agents
- [ ] T014 [IMPL] Implement agent list validation
- [ ] T015 [TEST] Write test for get_state_distribution returns dict
- [ ] T016 [IMPL] Implement get_state_distribution delegating to queries
- [ ] T017 [TEST] Write test for add_post adds to posts and increments metrics
- [ ] T018 [IMPL] Implement add_post method
- [ ] T019 [TEST] Write test for advance_round increments round_number
- [ ] T020 [IMPL] Implement advance_round method

### Result Types

- [ ] T021 [TEST] Write test for ActionResult dataclass
- [ ] T022 [IMPL] Implement ActionResult
- [ ] T023 [TEST] Write test for DecisionResult dataclass
- [ ] T024 [IMPL] Implement DecisionResult
- [ ] T025 [TEST] Write test for RoundResult dataclass
- [ ] T026 [IMPL] Implement RoundResult
- [ ] T027 [TEST] Write test for SimulationResult dataclass
- [ ] T028 [IMPL] Implement SimulationResult

---

## Phase 2: Triggers & Statechart Factory

Trigger determination and default statechart definition.

### Trigger Determination

- [ ] T029 [TEST] Write test for determine_trigger returns string
- [ ] T030 [IMPL] Implement determine_trigger function signature
- [ ] T031 [TEST] Write test for IDLE → "start_browsing"
- [ ] T032 [IMPL] Implement IDLE trigger case
- [ ] T033 [TEST] Write test for SCROLLING + feed → "sees_post"
- [ ] T034 [IMPL] Implement SCROLLING with feed trigger case
- [ ] T035 [TEST] Write test for SCROLLING + empty feed → "feed_empty"
- [ ] T036 [IMPL] Implement SCROLLING without feed trigger case
- [ ] T037 [TEST] Write test for EVALUATING → "decides"
- [ ] T038 [IMPL] Implement EVALUATING trigger case
- [ ] T039 [TEST] Write test for COMPOSING → "finishes_composing"
- [ ] T040 [IMPL] Implement COMPOSING trigger case
- [ ] T041 [TEST] Write test for ENGAGING_* → "finishes_engaging"
- [ ] T042 [IMPL] Implement ENGAGING states trigger case
- [ ] T043 [TEST] Write test for RESTING → "rested"
- [ ] T044 [IMPL] Implement RESTING trigger case

### Statechart Factory

- [ ] T045 [TEST] Write test for create_social_media_statechart returns Statechart
- [ ] T046 [IMPL] Implement factory function signature
- [ ] T047 [TEST] Write test for statechart has all AgentState values
- [ ] T048 [IMPL] Add all states to statechart
- [ ] T049 [TEST] Write test for statechart has initial state IDLE
- [ ] T050 [IMPL] Set initial state to IDLE
- [ ] T051 [TEST] Write test for transition IDLE → SCROLLING on "start_browsing"
- [ ] T052 [IMPL] Add start_browsing transition
- [ ] T053 [TEST] Write test for transition SCROLLING → EVALUATING on "sees_post"
- [ ] T054 [IMPL] Add sees_post transition
- [ ] T055 [TEST] Write test for transition SCROLLING → RESTING on "feed_empty"
- [ ] T056 [IMPL] Add feed_empty transition
- [ ] T057 [TEST] Write test for transitions from EVALUATING on "decides"
- [ ] T058 [IMPL] Add decides transitions to COMPOSING, ENGAGING_*, SCROLLING
- [ ] T059 [TEST] Write test for finishing transitions back to SCROLLING
- [ ] T060 [IMPL] Add finishes_composing and finishes_engaging transitions
- [ ] T061 [TEST] Write test for timeout transition from any state
- [ ] T062 [IMPL] Add timeout transitions

---

## Phase 3: Executors

Pipeline executors for agent rounds.

### Feed Retrieval Executor

- [ ] T063 [TEST] Write test for FeedRetrievalExecutor.execute returns list[Post]
- [ ] T064 [IMPL] Implement FeedRetrievalExecutor.execute
- [ ] T065 [TEST] Write test for executor uses agent.interests for retrieval
- [ ] T066 [IMPL] Wire up FeedRetriever.get_feed with agent interests

### Decision Executor

- [ ] T067 [TEST] Write test for AgentDecisionExecutor.execute calls agent.tick
- [ ] T068 [IMPL] Implement tick call at start of execute
- [ ] T069 [TEST] Write test for execute calls statechart.fire with correct args
- [ ] T070 [IMPL] Implement statechart.fire call
- [ ] T071 [TEST] Write test for execute detects multiple valid targets
- [ ] T072 [IMPL] Implement valid_targets check for ambiguous case
- [ ] T073 [TEST] Write test for execute calls reasoner.decide when ambiguous
- [ ] T074 [IMPL] Implement reasoner invocation
- [ ] T075 [TEST] Write test for execute calls agent.transition_to
- [ ] T076 [IMPL] Implement transition_to call
- [ ] T077 [TEST] Write test for execute returns DecisionResult
- [ ] T078 [IMPL] Implement DecisionResult construction and return
- [ ] T079 [TEST] Write test for action execution based on new state
- [ ] T080 [IMPL] Implement _execute_action method

### State Update Executor

- [ ] T081 [TEST] Write test for StateUpdateExecutor handles like action
- [ ] T082 [IMPL] Implement like handling (increment post.likes and metrics)
- [ ] T083 [TEST] Write test for executor handles reply action
- [ ] T084 [IMPL] Implement reply handling (increment + add post)
- [ ] T085 [TEST] Write test for executor handles reshare action
- [ ] T086 [IMPL] Implement reshare handling
- [ ] T087 [TEST] Write test for executor handles compose action
- [ ] T088 [IMPL] Implement compose handling (add new post)
- [ ] T089 [TEST] Write test for executor handles scroll action (no changes)
- [ ] T090 [IMPL] Implement scroll handling (no-op)

### Logging Executor

- [ ] T091 [TEST] Write test for LoggingExecutor.execute logs JSON entry
- [ ] T092 [IMPL] Implement structured JSON logging
- [ ] T093 [TEST] Write test for log entry contains required fields
- [ ] T094 [IMPL] Include timestamp, round, agent_id, trigger, states, action
- [ ] T095 [TEST] Write test for executor writes to file when configured
- [ ] T096 [IMPL] Implement file writing with flush

### Agent Round Executor

- [ ] T097 [TEST] Write test for AgentRoundExecutor coordinates pipeline
- [ ] T098 [IMPL] Implement AgentRoundExecutor.execute calling all executors
- [ ] T099 [TEST] Write test for executor returns DecisionResult
- [ ] T100 [IMPL] Wire up return value from decision executor

---

## Phase 4: Controller & Checkpoint

Round orchestration and state persistence.

### Checkpointer

- [ ] T101 [TEST] Write test for Checkpointer.save creates JSON file
- [ ] T102 [IMPL] Implement save method with JSON serialization
- [ ] T103 [TEST] Write test for saved file includes version field
- [ ] T104 [IMPL] Add version to CheckpointData
- [ ] T105 [TEST] Write test for file path includes round number
- [ ] T106 [IMPL] Implement filename pattern checkpoint_round_NNNN.json
- [ ] T107 [TEST] Write test for atomic write (temp file + rename)
- [ ] T108 [IMPL] Implement temp file pattern
- [ ] T109 [TEST] Write test for Checkpointer.load reconstructs state
- [ ] T110 [IMPL] Implement load method
- [ ] T111 [TEST] Write test for load validates version
- [ ] T112 [IMPL] Implement version check with ValueError
- [ ] T113 [TEST] Write test for latest_checkpoint finds most recent
- [ ] T114 [IMPL] Implement latest_checkpoint method
- [ ] T115 [TEST] Write test for checkpoint_for_round finds specific round
- [ ] T116 [IMPL] Implement checkpoint_for_round method

### Round Controller

- [ ] T117 [TEST] Write test for RoundController.run_simulation iterates rounds
- [ ] T118 [IMPL] Implement round iteration loop
- [ ] T119 [TEST] Write test for controller processes all agents each round
- [ ] T120 [IMPL] Implement agent iteration within round
- [ ] T121 [TEST] Write test for controller saves checkpoints at frequency
- [ ] T122 [IMPL] Implement checkpoint saving with frequency check
- [ ] T123 [TEST] Write test for controller skips checkpoints when dir is None
- [ ] T124 [IMPL] Implement checkpoint skip logic
- [ ] T125 [TEST] Write test for controller advances round_number
- [ ] T126 [IMPL] Implement state.advance_round call
- [ ] T127 [TEST] Write test for controller returns SimulationResult
- [ ] T128 [IMPL] Implement result construction
- [ ] T129 [TEST] Write test for run_round executes single round
- [ ] T130 [IMPL] Implement run_round method
- [ ] T131 [TEST] Write test for resume_from_checkpoint loads and continues
- [ ] T132 [IMPL] Implement resume_from_checkpoint method

---

## Phase 5: Integration

End-to-end integration and entry point.

### Config Integration

- [ ] T133 [TEST] Write test for configs/default.yaml has simulation section
- [ ] T134 [IMPL] Add simulation section to default.yaml
- [ ] T135 [TEST] Write test for load_config reads simulation section
- [ ] T136 [IMPL] Implement config loading function

### Module Exports

- [ ] T137 [TEST] Write test for prism/simulation/__init__.py exports
- [ ] T138 [IMPL] Create __init__.py with public exports
- [ ] T139 [TEST] Write test for prism/simulation/executors/__init__.py exports
- [ ] T140 [IMPL] Create executors/__init__.py

### Integration Test

- [ ] T141 [TEST] Write integration test: 3 agents × 2 rounds completes
- [ ] T142 [IMPL] Wire up all components in controller
- [ ] T143 [TEST] Write integration test: checkpoint/resume produces same state
- [ ] T144 [IMPL] Verify checkpoint serialization round-trips correctly
- [ ] T145 [TEST] Write integration test: state distribution logged each round
- [ ] T146 [IMPL] Verify logging executor output

### Entry Point

- [ ] T147 [TEST] Write test for main.py has run_simulation function
- [ ] T148 [IMPL] Add run_simulation to main.py
- [ ] T149 [SPEC] Run spec tests for 004-simulation-workflow-loop

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

- [ ] `uv run ruff check .` passes
- [ ] `uv run ruff format --check .` passes
- [ ] `uv run pytest tests/simulation/` passes
- [ ] Run spec tests with `/spec-tests` skill using `specs/tests/004-simulation-workflow-loop.md`
- [ ] All spec tests pass → feature complete
