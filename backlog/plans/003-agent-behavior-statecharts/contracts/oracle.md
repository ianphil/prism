# LLM Oracle Contract

## Purpose

The LLM Oracle resolves ambiguous state transitions where multiple target states are valid. Instead of arbitrary selection, the oracle uses the agent's profile and post context to make a decision that reflects the agent's personality.

## When Oracle is Invoked

1. `Statechart.fire()` finds multiple matching transitions
2. Caller detects ambiguity and calls oracle
3. Oracle returns the chosen target state
4. Caller updates agent state accordingly

## Oracle Interface

```python
class StatechartOracle:
    """LLM-based decision maker for ambiguous transitions."""

    def __init__(self, client: OllamaChatClient) -> None:
        """
        Initialize oracle with LLM client.

        Args:
            client: Ollama client for inference
        """
        ...

    async def decide(
        self,
        agent: "SocialAgent",
        current_state: AgentState,
        trigger: str,
        options: list[AgentState],
        context: Any = None,
    ) -> AgentState:
        """
        Decide which state transition to take.

        Args:
            agent: Agent making the decision
            current_state: Agent's current state
            trigger: Event that triggered the decision
            options: Valid target states to choose from
            context: Additional context (e.g., Post being evaluated)

        Returns:
            Chosen target state from options

        Raises:
            ValueError: If options is empty

        Note:
            On parse error, returns first option as fallback
        """
        ...
```

## Prompt Template

```python
def build_oracle_prompt(
    agent_name: str,
    agent_interests: list[str],
    agent_personality: str,
    current_state: AgentState,
    trigger: str,
    options: list[AgentState],
    context: Any,
) -> str:
    """Build prompt for oracle decision."""

    options_text = "\n".join(
        f"- {opt.value}: {STATE_DESCRIPTIONS[opt]}"
        for opt in options
    )

    context_text = format_context(context)  # e.g., Post details

    return f"""You are {agent_name}, a social media user.

Your interests: {', '.join(agent_interests)}
Your personality: {agent_personality}

You are currently in the "{current_state.value}" state and received the "{trigger}" event.

{context_text}

Choose your next state from these options:
{options_text}

Respond with JSON only:
{{"next_state": "<state_value>"}}
"""
```

## Response Parsing

```python
def parse_oracle_response(
    response_text: str,
    options: list[AgentState],
) -> AgentState:
    """
    Parse oracle response to AgentState.

    Args:
        response_text: Raw LLM response
        options: Valid options to validate against

    Returns:
        Parsed AgentState

    Raises:
        ValueError: If response doesn't match any option
    """
    try:
        data = json.loads(response_text)
        state_value = data.get("next_state", "").lower()

        for opt in options:
            if opt.value == state_value:
                return opt

        raise ValueError(f"Invalid state: {state_value}")

    except (json.JSONDecodeError, KeyError) as e:
        raise ValueError(f"Failed to parse oracle response: {e}")
```

## State Descriptions

Used in prompt to help LLM understand options:

```python
STATE_DESCRIPTIONS = {
    AgentState.IDLE: "Stop browsing, wait for next round",
    AgentState.SCROLLING: "Continue browsing without engaging",
    AgentState.EVALUATING: "Look more closely at this post",
    AgentState.COMPOSING: "Write a response or original content",
    AgentState.ENGAGING_LIKE: "Like this post",
    AgentState.ENGAGING_REPLY: "Reply to this post",
    AgentState.ENGAGING_RESHARE: "Reshare this post",
    AgentState.RESTING: "Take a break from activity",
}
```

## Error Handling

| Error | Handling |
|-------|----------|
| Empty options | Raise ValueError |
| LLM timeout | Log warning, return first option |
| JSON parse error | Log warning, return first option |
| Invalid state in response | Log warning, return first option |

## Usage Example

```python
from prism.statechart import StatechartOracle, AgentState

oracle = StatechartOracle(client=ollama_client)

# Ambiguous decision: agent evaluating a post
new_state = await oracle.decide(
    agent=agent,
    current_state=AgentState.EVALUATING,
    trigger="decides",
    options=[AgentState.COMPOSING, AgentState.SCROLLING],
    context=post,
)

agent.state = new_state
```

## Integration with Statechart

The oracle is NOT called by Statechart directly. The caller (simulation loop or agent) detects ambiguity and invokes oracle:

```python
# In simulation loop or agent method
new_state = chart.fire(agent, trigger, context)

if new_state is None:
    # No transition matched
    pass
elif isinstance(new_state, list):
    # Multiple matches (ambiguous) - not current design
    # Instead, caller checks valid_targets()
    pass
else:
    # Single match - apply transition
    agent.state = new_state

# Alternative: explicit ambiguity check
targets = chart.valid_targets(agent.state, trigger)
if len(targets) > 1:
    new_state = await oracle.decide(agent, agent.state, trigger, targets, context)
    agent.state = new_state
elif len(targets) == 1:
    agent.state = targets[0]
```
