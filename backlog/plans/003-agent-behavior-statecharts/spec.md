# Specification: Agent Behavior Statecharts

## Overview

### Problem Statement

Social agents currently make decisions via stateless LLM calls each simulation round. This creates several issues:

1. **Opaque behavior** — Cannot query "how many agents are composing right now?" or visualize state distribution
2. **No behavioral momentum** — Agent evaluates each post independently; no "I'm on a liking spree" or "lurking mode"
3. **Debugging difficulty** — Why did this cascade form? Hard to trace without explicit state transitions
4. **No stuck detection** — Agents can theoretically loop forever with no timeout mechanism

Without explicit behavioral states, researchers cannot understand agent dynamics, and the simulation cannot produce the traceable cascades needed for virality analysis.

### Solution Summary

Implement Harel-style statecharts to model agent behavioral states (Idle, Scrolling, Evaluating, Composing, Engaging substates). The statechart governs state transitions via triggers, guards, and actions, while the LLM serves as a "decision oracle" for ambiguous transitions. All state changes are logged for observability and cascade analysis.

### Business Value

| Benefit | Impact |
|---------|--------|
| Inspectable state | Query agent state distribution at any simulation round |
| Traceable transitions | Log every state change for cascade analysis and debugging |
| Behavioral modes | Agents exhibit realistic patterns (lurking, engaging bursts) |
| Stuck prevention | Timeout transitions auto-recover deadlocked agents |
| LLM as oracle | Statechart governs flow; LLM decides only ambiguous cases |

## User Stories

### Researcher

**As a researcher**, I want to query how many agents are in each behavioral state at any simulation round, so that I can analyze engagement patterns and cascade dynamics.

**Acceptance Criteria:**
- `state_distribution()` returns `{state: count}` dict for all agents
- `agents_in_state(state)` returns count for specific state
- State distribution queryable at any point during simulation

### Experimenter

**As an experimenter**, I want agent state transitions to be logged with timestamps and context, so that I can trace why specific cascades formed.

**Acceptance Criteria:**
- Each state transition recorded with `StateTransition(from_state, to_state, trigger, timestamp, context)`
- Agent maintains `state_history` list accessible for analysis
- History depth configurable to prevent unbounded memory growth

### Developer

**As a developer**, I want stuck agents to automatically recover via timeout transitions, so that the simulation doesn't deadlock.

**Acceptance Criteria:**
- Agents track `ticks_in_state` counter
- Timeout transitions fire when `ticks_in_state > threshold`
- Default timeout transitions from any active state to Scrolling or Idle
- Timeout threshold configurable per agent archetype

### Debugger

**As a developer debugging the simulation**, I want the LLM oracle to only be invoked for genuinely ambiguous transitions, so that inference costs stay manageable.

**Acceptance Criteria:**
- Clear transitions (timeout, explicit event) execute without LLM
- LLM oracle invoked only for `Evaluating → ?` decisions
- Oracle prompt includes agent profile, post content, and valid options
- Oracle response parsed to valid `AgentState`

## Functional Requirements

### FR-1: Agent State Enum

| Requirement | Description |
|-------------|-------------|
| FR-1.1 | `AgentState` enum defines all valid behavioral states |
| FR-1.2 | States include: IDLE, SCROLLING, EVALUATING, COMPOSING, ENGAGING_LIKE, ENGAGING_REPLY, ENGAGING_RESHARE, RESTING |
| FR-1.3 | States are string-valued for JSON serialization compatibility |

### FR-2: Transition Model

| Requirement | Description |
|-------------|-------------|
| FR-2.1 | `Transition` dataclass with trigger, source, target fields |
| FR-2.2 | Optional `guard` callable for conditional transitions |
| FR-2.3 | Optional `action` callable for side effects on transition |
| FR-2.4 | Transitions are immutable after definition |

### FR-3: Statechart Class

| Requirement | Description |
|-------------|-------------|
| FR-3.1 | `Statechart` holds state set and transition list |
| FR-3.2 | `fire(agent, trigger, context)` attempts transition, returns new state or None |
| FR-3.3 | `valid_triggers(state)` returns available triggers from given state |
| FR-3.4 | Guards evaluated in definition order; first match wins |
| FR-3.5 | Statechart is shared across agents (parameterized via agent fields) |

### FR-4: LLM Oracle Integration

| Requirement | Description |
|-------------|-------------|
| FR-4.1 | Oracle prompt builder constructs prompt from agent profile and post |
| FR-4.2 | Oracle invoked only for ambiguous transitions (Evaluating → ?) |
| FR-4.3 | Oracle returns valid `AgentState` from allowed options |
| FR-4.4 | Fallback to SCROLLING if oracle response invalid |

### FR-5: State History

| Requirement | Description |
|-------------|-------------|
| FR-5.1 | `StateTransition` records from_state, to_state, trigger, timestamp, context |
| FR-5.2 | Agent maintains `state_history: list[StateTransition]` |
| FR-5.3 | History depth configurable (default: 50 entries) |
| FR-5.4 | Old entries pruned when limit exceeded (FIFO) |

### FR-6: Timeout Transitions

| Requirement | Description |
|-------------|-------------|
| FR-6.1 | Agent tracks `ticks_in_state` counter, reset on state change |
| FR-6.2 | Timeout transition fires when `ticks_in_state > agent.timeout_threshold` |
| FR-6.3 | Default timeout transitions from active states to SCROLLING |
| FR-6.4 | Timeout threshold configurable per agent (default: 5 ticks) |

### FR-7: State Query Methods

| Requirement | Description |
|-------------|-------------|
| FR-7.1 | `agents_in_state(state, agents)` returns count of agents in given state |
| FR-7.2 | `state_distribution(agents)` returns `{state: count}` for all states |
| FR-7.3 | Query methods are standalone functions (not tied to simulation) |

### FR-8: SocialAgent Integration

| Requirement | Description |
|-------------|-------------|
| FR-8.1 | `SocialAgent` gains `state: AgentState` field (default: IDLE) |
| FR-8.2 | `SocialAgent` gains `state_history: list[StateTransition]` field |
| FR-8.3 | `SocialAgent` gains `ticks_in_state: int` field |
| FR-8.4 | Existing `decide()` method becomes internal; statechart drives flow |

## Non-Functional Requirements

### Performance

| Requirement | Target |
|-------------|--------|
| Transition evaluation | < 1ms for non-oracle transitions |
| Oracle call | Uses existing LLM latency (~500ms for Ollama local) |
| State query | O(n) where n = number of agents |
| Memory per agent | < 10KB for state history (50 entries) |

### Scalability

| Requirement | Target |
|-------------|--------|
| Agent count | Statechart supports 500 concurrent agents |
| Transition definitions | Statechart handles 50+ transitions without degradation |

### Reliability

| Requirement | Target |
|-------------|--------|
| Invalid guard | Failed guards return False (safe default per SCXML) |
| Oracle parse error | Fallback to SCROLLING state |
| Missing trigger | `fire()` returns None (no transition) |

## Scope

### In Scope

- `AgentState` enum with all behavioral states
- `Transition` dataclass with guard and action support
- `Statechart` class with fire(), valid_triggers()
- LLM oracle for ambiguous Evaluating transitions
- State history tracking with configurable depth
- Timeout transitions for stuck agent recovery
- State query functions (agents_in_state, state_distribution)
- Integration with existing `SocialAgent` class
- Unit tests for all components

### Out of Scope

- Visual statechart editor (use code definitions)
- Parallel/concurrent state regions (initial simplicity)
- Full UML statechart compliance (pragmatic subset)
- Deep hierarchy (keep states flat initially)
- History states (shallow history; resume not needed for MVP)

### Future Considerations

- Hierarchical states (Engaging as composite with Like/Reply/Reshare substates)
- Parallel regions for modeling concurrent behaviors
- Entry/exit actions on composite states
- SCXML export for visualization tools
- Rate-based probabilistic transitions

## Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| State queryable | All agents report valid state | `agent.state in AgentState` |
| Transitions traced | All state changes logged | `len(agent.state_history) > 0` after activity |
| Timeout works | Stuck agents recover | Agent at `ticks_in_state=10` transitions to SCROLLING |
| Oracle invoked | LLM called for ambiguous only | Logs show oracle calls only for Evaluating→? |
| No deadlocks | Simulation completes | 100-agent, 10-round simulation finishes |

## Assumptions

1. Existing `SocialAgent` class can be extended with new fields
2. LLM response parsing is reliable enough for oracle use
3. 50-entry state history is sufficient for debugging without memory pressure
4. Single-threaded simulation loop (no concurrent state access concerns)
5. Agent thresholds (engagement_threshold, timeout_threshold) can be added to profile

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Statechart complexity creep | Medium | Medium | Start minimal; add features only when needed |
| Oracle response parsing fails | Medium | Low | Fallback to SCROLLING; log warning |
| State explosion with substates | Low | Medium | Keep states flat for MVP; refactor later if needed |
| Memory growth from history | Low | Medium | Configurable depth limit with FIFO pruning |
| Guard evaluation expensive | Low | Low | Guards are simple lambdas; profile if needed |

## Glossary

| Term | Definition |
|------|------------|
| Statechart | Extended finite state machine with hierarchy and guards (Harel, 1987) |
| State | A behavioral mode representing agent's current activity |
| Transition | Atomic move from one state to another, triggered by event |
| Trigger | Event that can cause a transition (e.g., "sees_post", "timeout") |
| Guard | Boolean condition that must be true for transition to fire |
| Action | Side effect executed when transition fires |
| Oracle | LLM used to decide ambiguous transitions |
| Tick | One simulation round; used for timeout counting |
