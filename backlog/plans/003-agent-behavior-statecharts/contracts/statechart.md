# Statechart Contract

## AgentState Enum

```python
from enum import Enum

class AgentState(str, Enum):
    """Behavioral states for social agents."""

    IDLE = "idle"
    SCROLLING = "scrolling"
    EVALUATING = "evaluating"
    COMPOSING = "composing"
    ENGAGING_LIKE = "engaging_like"
    ENGAGING_REPLY = "engaging_reply"
    ENGAGING_RESHARE = "engaging_reshare"
    RESTING = "resting"
```

### Requirements

- Inherits from `str` for JSON serialization
- Values are lowercase for consistency
- Enum is exhaustive; adding states requires code change

---

## Transition Dataclass

```python
from dataclasses import dataclass
from typing import Callable, Any

@dataclass(frozen=True)
class Transition:
    """Defines a state transition in the statechart."""

    trigger: str
    source: AgentState
    target: AgentState
    guard: Callable[[Any, Any], bool] | None = None
    action: Callable[[Any, Any], None] | None = None
```

### Field Specifications

| Field | Type | Constraints |
|-------|------|-------------|
| `trigger` | str | Non-empty; event name |
| `source` | AgentState | Must be valid state |
| `target` | AgentState | Must be valid state |
| `guard` | callable or None | Signature: `(agent, context) -> bool` |
| `action` | callable or None | Signature: `(agent, context) -> None` |

### Guard Behavior

- Called with `(agent, context)` where context is typically a `Post` or None
- Must return boolean (truthy/falsy coerced to bool)
- On exception: treat as False (SCXML conformance)
- Evaluated in transition definition order

### Action Behavior

- Called after guard passes, before state update
- Used for side effects (logging, metrics, etc.)
- On exception: log warning, continue with transition

---

## StateTransition Record

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class StateTransition:
    """Records a historical state transition."""

    from_state: AgentState
    to_state: AgentState
    trigger: str
    timestamp: datetime
    context: dict | None = None
```

### Requirements

- Timestamp is UTC
- Context is optional; used for debugging (e.g., `{"post_id": "..."}`)
- Immutable after creation

---

## Statechart Class

```python
class Statechart:
    """State machine engine for agent behavior."""

    def __init__(
        self,
        states: set[AgentState],
        transitions: list[Transition],
        initial: AgentState,
    ) -> None:
        """
        Initialize statechart.

        Args:
            states: Set of valid states
            transitions: List of transition definitions
            initial: Starting state for new agents

        Raises:
            ValueError: If initial not in states
            ValueError: If any transition source/target not in states
        """
        ...

    def fire(
        self,
        agent: Any,
        trigger: str,
        context: Any = None,
    ) -> AgentState | None:
        """
        Attempt to fire a transition.

        Args:
            agent: Agent instance (must have .state attribute)
            trigger: Event name to match
            context: Additional context (e.g., Post being evaluated)

        Returns:
            New state if transition fired, None if no valid transition

        Note:
            Does NOT update agent.state; caller must do that
        """
        ...

    def valid_triggers(self, state: AgentState) -> list[str]:
        """
        Return triggers available from given state.

        Args:
            state: Current state to check

        Returns:
            List of trigger names that have transitions from this state
        """
        ...

    def valid_targets(
        self,
        state: AgentState,
        trigger: str,
    ) -> list[AgentState]:
        """
        Return possible target states for trigger from state.

        Args:
            state: Current state
            trigger: Event name

        Returns:
            List of possible target states (may be empty)
        """
        ...
```

### fire() Behavior

1. Find all transitions matching `trigger` from `agent.state`
2. For each transition (in definition order):
   - If guard is None → transition matches
   - If guard returns True → transition matches
   - If guard raises → treat as False, continue
3. If exactly one match → return target state
4. If no matches → return None
5. If multiple matches → ambiguous (caller should invoke oracle)

### Construction Validation

```python
# Validates at construction time
chart = Statechart(
    states={AgentState.IDLE, AgentState.SCROLLING},
    transitions=[
        Transition("go", AgentState.IDLE, AgentState.SCROLLING),
        Transition("back", AgentState.SCROLLING, AgentState.IDLE),
    ],
    initial=AgentState.IDLE,
)

# Raises ValueError: invalid source state
chart = Statechart(
    states={AgentState.IDLE},
    transitions=[
        Transition("go", AgentState.SCROLLING, AgentState.IDLE),  # Error!
    ],
    initial=AgentState.IDLE,
)
```

---

## Usage Example

```python
from prism.statechart import Statechart, Transition, AgentState

# Define statechart
chart = Statechart(
    states=set(AgentState),
    transitions=[
        Transition(
            trigger="feed_ready",
            source=AgentState.IDLE,
            target=AgentState.SCROLLING,
        ),
        Transition(
            trigger="sees_post",
            source=AgentState.SCROLLING,
            target=AgentState.EVALUATING,
        ),
        Transition(
            trigger="decides",
            source=AgentState.EVALUATING,
            target=AgentState.COMPOSING,
            guard=lambda agent, post: post.velocity > agent.engagement_threshold,
        ),
        Transition(
            trigger="decides",
            source=AgentState.EVALUATING,
            target=AgentState.SCROLLING,
            # No guard = fallback
        ),
    ],
    initial=AgentState.IDLE,
)

# Use statechart
agent.state = AgentState.IDLE
new_state = chart.fire(agent, "feed_ready")
if new_state:
    agent.state = new_state  # SCROLLING
```
