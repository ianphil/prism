# Agent State Management Contract

## SocialAgent Extensions

New fields and methods added to the existing `SocialAgent` class for statechart integration.

## New Fields

```python
class SocialAgent:
    # Existing fields...
    agent_id: str
    name: str
    interests: list[str]
    personality: str
    _client: OllamaChatClient

    # NEW: Statechart integration
    state: AgentState = AgentState.IDLE
    state_history: list[StateTransition] = field(default_factory=list)
    ticks_in_state: int = 0

    # NEW: Behavioral thresholds (for guards)
    engagement_threshold: float = 0.5
    timeout_threshold: int = 5
    max_history_depth: int = 50
```

### Field Specifications

| Field | Type | Default | Constraints |
|-------|------|---------|-------------|
| `state` | AgentState | IDLE | Must be valid enum value |
| `state_history` | list[StateTransition] | [] | Max length = max_history_depth |
| `ticks_in_state` | int | 0 | >= 0 |
| `engagement_threshold` | float | 0.5 | 0.0 to 1.0 |
| `timeout_threshold` | int | 5 | > 0 |
| `max_history_depth` | int | 50 | > 0 |

## New Methods

### transition_to()

```python
def transition_to(
    self,
    new_state: AgentState,
    trigger: str,
    context: dict | None = None,
) -> None:
    """
    Update agent state and record transition.

    Args:
        new_state: State to transition to
        trigger: Event that caused the transition
        context: Optional context for history record

    Note:
        - Records StateTransition in history
        - Resets ticks_in_state to 0
        - Prunes history if over max_history_depth
    """
    if new_state == self.state:
        return  # No-op for self-transitions

    record = StateTransition(
        from_state=self.state,
        to_state=new_state,
        trigger=trigger,
        timestamp=datetime.utcnow(),
        context=context,
    )

    self.state_history.append(record)

    # FIFO pruning
    while len(self.state_history) > self.max_history_depth:
        self.state_history.pop(0)

    self.state = new_state
    self.ticks_in_state = 0
```

### tick()

```python
def tick(self) -> None:
    """
    Increment ticks_in_state counter.

    Called once per simulation round for timeout detection.
    """
    self.ticks_in_state += 1
```

### is_timed_out()

```python
def is_timed_out(self) -> bool:
    """
    Check if agent has been in current state too long.

    Returns:
        True if ticks_in_state > timeout_threshold
    """
    return self.ticks_in_state > self.timeout_threshold
```

### should_engage()

```python
def should_engage(self, post: "Post") -> bool:
    """
    Guard function for engagement transitions.

    Args:
        post: Post being evaluated

    Returns:
        True if agent should engage based on thresholds
    """
    # Simple heuristic; can be made more sophisticated
    relevance = self._compute_relevance(post)
    return relevance > self.engagement_threshold

def _compute_relevance(self, post: "Post") -> float:
    """Compute relevance score for post based on agent interests."""
    # Placeholder: count keyword matches
    text_lower = post.text.lower()
    matches = sum(1 for interest in self.interests if interest.lower() in text_lower)
    return min(1.0, matches / max(1, len(self.interests)))
```

### get_state_summary()

```python
def get_state_summary(self) -> dict:
    """
    Return summary of current state for debugging.

    Returns:
        Dict with state, ticks, and recent history
    """
    return {
        "agent_id": self.agent_id,
        "state": self.state.value,
        "ticks_in_state": self.ticks_in_state,
        "history_length": len(self.state_history),
        "recent_transitions": [
            {
                "from": t.from_state.value,
                "to": t.to_state.value,
                "trigger": t.trigger,
            }
            for t in self.state_history[-5:]  # Last 5
        ],
    }
```

## Constructor Updates

```python
def __init__(
    self,
    agent_id: str,
    name: str,
    interests: list[str],
    personality: str,
    client: OllamaChatClient,
    temperature: float = 0.7,
    max_tokens: int = 512,
    # NEW parameters
    engagement_threshold: float = 0.5,
    timeout_threshold: int = 5,
    max_history_depth: int = 50,
) -> None:
    # Existing initialization...

    # NEW: Statechart state
    self.state = AgentState.IDLE
    self.state_history: list[StateTransition] = []
    self.ticks_in_state = 0

    # NEW: Thresholds
    self.engagement_threshold = engagement_threshold
    self.timeout_threshold = timeout_threshold
    self.max_history_depth = max_history_depth
```

## State Query Functions

Standalone functions for querying state across multiple agents:

```python
def agents_in_state(state: AgentState, agents: list["SocialAgent"]) -> int:
    """
    Count agents in a specific state.

    Args:
        state: State to count
        agents: List of agents to check

    Returns:
        Number of agents in the given state
    """
    return sum(1 for agent in agents if agent.state == state)


def state_distribution(agents: list["SocialAgent"]) -> dict[AgentState, int]:
    """
    Get distribution of agents across all states.

    Args:
        agents: List of agents to analyze

    Returns:
        Dict mapping each state to count of agents in that state
    """
    from collections import Counter
    counts = Counter(agent.state for agent in agents)
    return {state: counts.get(state, 0) for state in AgentState}
```

## Usage Example

```python
from prism.agents import SocialAgent
from prism.statechart import AgentState, Statechart

# Create agent with custom thresholds
agent = SocialAgent(
    agent_id="agent_001",
    name="Alex",
    interests=["AI", "Python"],
    personality="curious developer",
    client=ollama_client,
    engagement_threshold=0.3,  # Engages easily
    timeout_threshold=3,       # Short patience
)

# Simulation loop
chart = get_social_agent_chart()

while simulation_running:
    trigger = determine_trigger(agent, context)
    new_state = chart.fire(agent, trigger, context)

    if new_state:
        agent.transition_to(new_state, trigger, {"post_id": post.id})

    agent.tick()

    if agent.is_timed_out():
        agent.transition_to(AgentState.SCROLLING, "timeout")

# Query state distribution
from prism.statechart import state_distribution
dist = state_distribution(all_agents)
print(f"Agents composing: {dist[AgentState.COMPOSING]}")
```
