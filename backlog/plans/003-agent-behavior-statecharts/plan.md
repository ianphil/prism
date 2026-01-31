# Plan: Agent Behavior Statecharts

## Summary

Implement a custom Harel-style statechart engine (~200 lines) to model agent behavioral states. The statechart governs state transitions via triggers and guards, with the LLM serving as a decision oracle for ambiguous transitions. All state changes are recorded for observability and cascade analysis.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        prism/statechart/                             │
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐   │
│  │ AgentState   │    │ Transition   │    │ StateTransition      │   │
│  │ (enum)       │    │ (dataclass)  │    │ (history record)     │   │
│  └──────────────┘    └──────────────┘    └──────────────────────┘   │
│         │                   │                       │                │
│         └─────────┬─────────┘                       │                │
│                   ▼                                 │                │
│          ┌────────────────┐                         │                │
│          │   Statechart   │                         │                │
│          │  • states      │                         │                │
│          │  • transitions │                         │                │
│          │  • fire()      │◀────────────────────────┘                │
│          │  • valid_*()   │                                          │
│          └───────┬────────┘                                          │
│                  │                                                   │
│                  ▼                                                   │
│          ┌────────────────┐                                          │
│          │  LLM Oracle    │  (for ambiguous transitions)             │
│          │  • prompt      │                                          │
│          │  • parse       │                                          │
│          └────────────────┘                                          │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Query Functions                            │   │
│  │  • agents_in_state(state, agents) → int                       │   │
│  │  • state_distribution(agents) → dict[AgentState, int]         │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

## Detailed Architecture

### State Machine Flow

```
                    ┌─────────────────────────────────────────┐
                    │             Simulation Loop             │
                    │  for each agent:                        │
                    │    trigger = determine_trigger(context) │
                    │    new_state = chart.fire(agent, ...)   │
                    └─────────────────┬───────────────────────┘
                                      │
                                      ▼
                    ┌─────────────────────────────────────────┐
                    │           Statechart.fire()             │
                    │                                         │
                    │  1. Find transitions matching trigger   │
                    │  2. Filter by source == agent.state     │
                    │  3. Evaluate guards in order            │
                    │     ┌─────────────────────────────────┐ │
                    │     │ Guard evaluation:               │ │
                    │     │ • Try guard(agent, context)     │ │
                    │     │ • On exception → False          │ │
                    │     │ • First True guard wins         │ │
                    │     └─────────────────────────────────┘ │
                    │  4. If ambiguous → call LLM oracle      │
                    │  5. Execute action (if any)             │
                    │  6. Update agent.state                  │
                    │  7. Record StateTransition in history   │
                    │  8. Reset ticks_in_state                │
                    └─────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Role | Integrates With |
|-----------|------|-----------------|
| `AgentState` | Enum of all valid behavioral states | Transition, SocialAgent |
| `Transition` | Defines trigger, source, target, guard, action | Statechart |
| `StateTransition` | History record with timestamps | SocialAgent.state_history |
| `Statechart` | Core engine: fire(), valid_triggers() | SocialAgent, Oracle |
| `Oracle` | LLM decision for ambiguous transitions | Statechart, OllamaChatClient |
| `Query functions` | State distribution analysis | Simulation manager |

### Data Flow: Agent Evaluates Post

```
SocialAgent                 Statechart                  LLM Oracle
     │                           │                           │
     │  fire("sees_post", post)  │                           │
     │─────────────────────────▶│                           │
     │                           │                           │
     │                           │ Find transitions from     │
     │                           │ SCROLLING with trigger    │
     │                           │ "sees_post"               │
     │                           │                           │
     │                           │ Evaluate guards...        │
     │                           │ → matches EVALUATING      │
     │                           │                           │
     │         EVALUATING        │                           │
     │◀─────────────────────────│                           │
     │                           │                           │
     │  fire("decides", post)    │                           │
     │─────────────────────────▶│                           │
     │                           │                           │
     │                           │ Multiple valid targets:   │
     │                           │ COMPOSING, SCROLLING      │
     │                           │                           │
     │                           │  query_oracle(agent,post) │
     │                           │─────────────────────────▶│
     │                           │                           │
     │                           │    COMPOSING (choice)     │
     │                           │◀─────────────────────────│
     │                           │                           │
     │          COMPOSING        │                           │
     │◀─────────────────────────│                           │
     │                           │                           │
     │  Record StateTransition   │                           │
     │  in state_history         │                           │
     └───────────────────────────┴───────────────────────────┘
```

## File Structure

```
prism/
├── statechart/                    # NEW: Statechart module
│   ├── __init__.py                # NEW: Export public API
│   ├── states.py                  # NEW: AgentState enum
│   ├── transitions.py             # NEW: Transition, StateTransition
│   ├── statechart.py              # NEW: Statechart class
│   ├── oracle.py                  # NEW: LLM oracle for decisions
│   └── queries.py                 # NEW: State query functions
│
├── agents/
│   └── social_agent.py            # MODIFY: Add state, state_history, ticks_in_state
│
tests/
├── statechart/                    # NEW: Statechart tests
│   ├── __init__.py
│   ├── test_states.py
│   ├── test_transitions.py
│   ├── test_statechart.py
│   ├── test_oracle.py
│   ├── test_queries.py
│   └── test_integration.py
```

## Critical: LLM Oracle Design

**Problem**: How do we decide when to invoke the expensive LLM oracle vs. using deterministic guards?

**Solution**: Oracle is invoked only when:
1. Multiple transitions match the trigger from the current state
2. Multiple guards evaluate to True (ambiguous case)
3. The transition is explicitly marked as requiring oracle decision

For `Evaluating → ?` transitions, the guard can check thresholds:
- `post.relevance > agent.high_threshold` → COMPOSING (deterministic)
- `post.relevance < agent.low_threshold` → SCROLLING (deterministic)
- Otherwise → LLM oracle decides

```python
# Deterministic guard
def high_engagement_guard(agent, post):
    return post.velocity > 100 or agent.is_interested(post)

# Oracle-required transition (no guard, or guard returns "needs_oracle")
Transition(
    trigger="decides",
    source=AgentState.EVALUATING,
    target=None,  # Oracle will decide
    guard=lambda a, p: "needs_oracle",  # Special marker
)
```

## Implementation Phases

See `tasks.md` for detailed breakdown. Summary:

1. **Phase 1**: Core types (AgentState, Transition, StateTransition)
2. **Phase 2**: Statechart engine (fire, valid_triggers)
3. **Phase 3**: LLM Oracle integration
4. **Phase 4**: Timeout transitions
5. **Phase 5**: SocialAgent integration
6. **Phase 6**: State queries and final validation

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Statechart scope | Shared + parameterized | One definition; behavior varies via agent thresholds |
| State representation | Enum (str) | JSON-serializable, exhaustive pattern matching |
| Guard fail-safe | Return False on exception | SCXML conformance; prevents crashes |
| Oracle invocation | Explicit marker or multiple matches | Minimize LLM calls; deterministic when possible |
| History depth | Configurable (default: 50) | Balance debugging vs memory |
| Timeout mechanism | ticks_in_state counter | Simple; no external timer dependency |

## Configuration Example

```yaml
# configs/default.yaml additions
statechart:
  default_timeout_ticks: 5
  max_history_depth: 50
  oracle_enabled: true

# Agent-specific thresholds (set at construction)
# agent = SocialAgent(
#     engagement_threshold=0.5,
#     timeout_threshold=5,
#     ...
# )
```

## Files to Modify

| File | Change |
|------|--------|
| `prism/agents/social_agent.py` | Add state, state_history, ticks_in_state fields |
| `configs/default.yaml` | Add statechart section (optional config) |
| `prism/llm/config.py` | Potentially add StatechartConfig |

## New Files

| File | Purpose |
|------|---------|
| `prism/statechart/__init__.py` | Module exports |
| `prism/statechart/states.py` | AgentState enum |
| `prism/statechart/transitions.py` | Transition and StateTransition dataclasses |
| `prism/statechart/statechart.py` | Statechart class (~150 lines) |
| `prism/statechart/oracle.py` | LLM oracle for ambiguous transitions |
| `prism/statechart/queries.py` | State query functions |

## Verification

1. Unit tests pass: `uv run pytest tests/statechart/`
2. Integration test: Agent transitions through states correctly
3. Oracle test: LLM invoked only for ambiguous cases
4. Timeout test: Stuck agent recovers after N ticks
5. Spec tests pass: `specs/tests/003-agent-behavior-statecharts.md`

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Statechart complexity creep | Start minimal; resist adding features until needed |
| Oracle response parsing fails | Fallback to SCROLLING; log warning for debugging |
| Performance impact | Guards are simple lambdas; oracle only when needed |
| Memory from history | Configurable depth with FIFO pruning |

## Limitations (MVP)

1. **No composite states** — ENGAGING_LIKE/REPLY/RESHARE are flat, not nested under Engaging. Acceptable because we don't need common exit transitions from Engaging.

2. **No parallel regions** — Agent can only be in one state. Acceptable for social media browsing model.

3. **No deep history** — Agents don't resume previous substate after interruption. Acceptable because interruptions start fresh.

4. **Single statechart definition** — All agents share the same state machine. Acceptable because diversity comes from parameterized guards.

## References

- [W3C SCXML Specification](https://www.w3.org/TR/scxml/)
- [AnyLogic Statecharts](https://anylogic.help/anylogic/statecharts/statecharts.html)
- Internal: `aidocs/statecharts-research.md`
