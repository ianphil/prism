# Data Model: Agent Behavior Statecharts

## Entities

### AgentState

Enum representing all valid behavioral states for a social agent.

| Value | Description |
|-------|-------------|
| `IDLE` | Not actively browsing; waiting for next round |
| `SCROLLING` | Browsing feed, not focused on any specific post |
| `EVALUATING` | Considering a specific post for engagement |
| `COMPOSING` | Drafting content (reply or original post) |
| `ENGAGING_LIKE` | Performing like action on a post |
| `ENGAGING_REPLY` | Posting a reply to a post |
| `ENGAGING_RESHARE` | Resharing a post with commentary |
| `RESTING` | Cooling down after activity burst |

**Invariants:**
- State values are lowercase strings for JSON serialization
- State enum is exhaustive; no invalid states possible
- Enum inherits from `str` for easy comparison and serialization

### Transition

Defines a state transition in the statechart.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `trigger` | str | Yes | — | Event name that causes this transition |
| `source` | AgentState | Yes | — | State this transition originates from |
| `target` | AgentState | Yes | — | State this transition leads to |
| `guard` | Callable[[Any, Any], bool] \| None | No | None | Condition that must be True for transition |
| `action` | Callable[[Any, Any], None] \| None | No | None | Side effect executed on transition |

**Invariants:**
- `source` and `target` must be valid `AgentState` values
- `trigger` must be non-empty string
- `guard` signature: `(agent, context) -> bool`
- `action` signature: `(agent, context) -> None`
- Transition is immutable after creation

### StateTransition

Records a historical state transition for debugging and analysis.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `from_state` | AgentState | Yes | — | State before transition |
| `to_state` | AgentState | Yes | — | State after transition |
| `trigger` | str | Yes | — | Event that caused the transition |
| `timestamp` | datetime | Yes | — | When the transition occurred |
| `context` | dict \| None | No | None | Additional context (post ID, etc.) |

**Relationships:**
- Owned by `SocialAgent.state_history`
- Multiple StateTransitions per agent (up to max_history_depth)

**Invariants:**
- `from_state != to_state` (self-transitions not recorded)
- `timestamp` is UTC
- `context` is optional; used for debugging

### Statechart

The state machine engine that manages transitions.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `states` | set[AgentState] | Yes | — | All valid states in this chart |
| `transitions` | list[Transition] | Yes | — | All transition definitions |
| `initial` | AgentState | Yes | — | Starting state for new agents |

**Invariants:**
- All transition sources and targets must be in `states`
- `initial` must be in `states`
- Transitions are evaluated in list order (first match wins)

### SocialAgent Extensions

New fields added to the existing `SocialAgent` class.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `state` | AgentState | No | IDLE | Current behavioral state |
| `state_history` | list[StateTransition] | No | [] | Record of state changes |
| `ticks_in_state` | int | No | 0 | Counter for timeout detection |
| `engagement_threshold` | float | No | 0.5 | Threshold for engagement guards |
| `timeout_threshold` | int | No | 5 | Ticks before timeout transition |
| `max_history_depth` | int | No | 50 | Max entries in state_history |

**Relationships:**
- Uses shared `Statechart` instance for transitions
- Owns `state_history` list
- References `OllamaChatClient` for oracle calls

**Invariants:**
- `state` is always a valid `AgentState`
- `ticks_in_state >= 0`
- `len(state_history) <= max_history_depth`
- `0.0 <= engagement_threshold <= 1.0`
- `timeout_threshold > 0`

## State Transitions

### Agent Lifecycle

```
                              ┌────────────────────────────────────────┐
                              │                                        │
     ┌───────┐  feed_ready    │   ┌──────────┐    sees_post           │
     │ IDLE  │───────────────▶│   │SCROLLING │─────────────────┐      │
     └───────┘                │   └──────────┘                 │      │
         ▲                    │        │                       ▼      │
         │                    │        │ timeout        ┌───────────┐ │
         │   round_ends       │        ▼                │EVALUATING │ │
         │                    │   ┌──────────┐          └───────────┘ │
         └────────────────────│───│ RESTING  │               │        │
                              │   └──────────┘          ┌────┴────┐   │
                              │        ▲                │         │   │
                              │        │           ignores    decides │
                              │   action_done           │     engage  │
                              │        │                ▼         │   │
                              │   ┌────┴────┐      SCROLLING      │   │
                              │   │ENGAGING │                     │   │
                              │   │ • LIKE  │◀────────────────────┘   │
                              │   │ • REPLY │                         │
                              │   │ •RESHARE│                         │
                              │   └─────────┘                         │
                              │                                       │
                              └───────────────────────────────────────┘
```

### State Descriptions

| State | Entry Condition | Exit Conditions | Typical Duration |
|-------|-----------------|-----------------|------------------|
| IDLE | Round ends | feed_ready trigger | 1 tick |
| SCROLLING | Feed available | sees_post, timeout | 1-3 ticks |
| EVALUATING | Post in view | decides trigger | 1 tick |
| COMPOSING | Decided to engage | compose_done | 1-2 ticks |
| ENGAGING_* | Content ready | action_done | 1 tick |
| RESTING | After engagement | timeout | 1-2 ticks |

### Trigger Catalog

| Trigger | Description | Source States |
|---------|-------------|---------------|
| `feed_ready` | Feed retrieved for agent | IDLE |
| `sees_post` | Agent notices a post | SCROLLING |
| `decides` | Agent makes engagement decision | EVALUATING |
| `ignores` | Agent skips post | EVALUATING |
| `compose_done` | Content drafted | COMPOSING |
| `action_done` | Engagement action complete | ENGAGING_* |
| `round_ends` | Simulation round complete | Any active |
| `timeout` | Stuck in state too long | Any active |

## Data Flow

### State Transition Recording

```
┌────────────────┐      fire(trigger)      ┌────────────────┐
│  SocialAgent   │ ─────────────────────▶  │   Statechart   │
│                │                         │                │
│  state: S1     │                         │                │
│  ticks_in_: 3  │      new_state: S2      │                │
│  history: [...]│ ◀───────────────────── │                │
└────────────────┘                         └────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│  Agent updates:                                         │
│  1. state = S2                                          │
│  2. ticks_in_state = 0                                  │
│  3. state_history.append(StateTransition(               │
│         from_state=S1,                                  │
│         to_state=S2,                                    │
│         trigger="sees_post",                            │
│         timestamp=datetime.utcnow(),                    │
│         context={"post_id": "..."}                      │
│     ))                                                  │
│  4. if len(state_history) > max_history_depth:          │
│         state_history.pop(0)  # FIFO pruning            │
└─────────────────────────────────────────────────────────┘
```

### Oracle Decision Flow

```
┌──────────────┐                    ┌──────────────┐
│  Statechart  │   ambiguous case   │  LLM Oracle  │
│              │ ─────────────────▶ │              │
│              │                    │              │
│ Candidates:  │   build_prompt()   │              │
│ • COMPOSING  │                    │              │
│ • SCROLLING  │   ◀─────────────── │              │
│              │                    │              │
│              │   agent.run()      │              │
│              │ ─────────────────▶ │              │
│              │                    │              │
│              │   {"next_state":   │              │
│              │    "composing"}    │              │
│ new_state:   │ ◀─────────────── │              │
│ COMPOSING    │                    │              │
└──────────────┘                    └──────────────┘
```

## Validation Summary

| Entity | Rule | Error |
|--------|------|-------|
| AgentState | Value in enum | ValueError |
| Transition.source | Valid AgentState | ValueError at construction |
| Transition.target | Valid AgentState | ValueError at construction |
| Transition.trigger | Non-empty string | ValueError |
| Statechart.initial | In states set | ValueError |
| StateTransition.from_state | != to_state | Skip recording (no-op) |
| SocialAgent.state | Valid AgentState | TypeError |
| SocialAgent.ticks_in_state | >= 0 | ValueError |
| SocialAgent.engagement_threshold | 0.0 to 1.0 | ValueError |
| SocialAgent.timeout_threshold | > 0 | ValueError |

## Serialization

### JSON Export (for debugging/logging)

```json
{
  "agent_id": "agent_001",
  "current_state": "evaluating",
  "ticks_in_state": 2,
  "state_history": [
    {
      "from_state": "idle",
      "to_state": "scrolling",
      "trigger": "feed_ready",
      "timestamp": "2026-01-30T10:00:00Z",
      "context": null
    },
    {
      "from_state": "scrolling",
      "to_state": "evaluating",
      "trigger": "sees_post",
      "timestamp": "2026-01-30T10:00:01Z",
      "context": {"post_id": "post_123"}
    }
  ]
}
```

### Statechart Definition (code)

```python
social_agent_chart = Statechart(
    states=set(AgentState),
    transitions=[
        Transition("feed_ready", AgentState.IDLE, AgentState.SCROLLING),
        Transition("sees_post", AgentState.SCROLLING, AgentState.EVALUATING),
        Transition("ignores", AgentState.EVALUATING, AgentState.SCROLLING),
        Transition("decides", AgentState.EVALUATING, AgentState.COMPOSING,
                   guard=lambda a, p: a.should_engage(p)),
        Transition("decides", AgentState.EVALUATING, AgentState.SCROLLING),
        Transition("compose_done", AgentState.COMPOSING, AgentState.ENGAGING_REPLY,
                   guard=lambda a, _: a.pending_action == "reply"),
        # ... etc
    ],
    initial=AgentState.IDLE,
)
```
