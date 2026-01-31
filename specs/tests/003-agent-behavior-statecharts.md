---
target:
  - prism/statechart/states.py
  - prism/statechart/transitions.py
  - prism/statechart/statechart.py
  - prism/statechart/reasoner.py
  - prism/statechart/queries.py
  - prism/agents/social_agent.py
---

# Agent Behavior Statecharts Spec Tests

Validates that PRISM's statechart system provides explicit behavioral states for agents, governed transitions with guards, LLM reasoner integration for ambiguous decisions, state history tracking, and timeout recovery for stuck agents.

## Agent State Enum

### AgentState defines all behavioral states as string enum

Researchers need to query agent state distribution at any simulation round. Without a well-defined enum, state tracking becomes stringly-typed and error-prone, breaking observability.

```
Given the prism/statechart/states.py file
When examining the AgentState class
Then it is an Enum that also inherits from str
And it has an IDLE member with value "idle"
And it has a SCROLLING member with value "scrolling"
And it has an EVALUATING member with value "evaluating"
And it has a COMPOSING member with value "composing"
And it has ENGAGING_LIKE, ENGAGING_REPLY, and ENGAGING_RESHARE members
And it has a RESTING member with value "resting"
```

## Transition Model

### Transition dataclass defines state transitions with guards and actions

The statechart needs transitions that can conditionally fire based on agent/post context. Without guard support, all agents would behave identically regardless of personality or interests.

```
Given the prism/statechart/transitions.py file
When examining the Transition class
Then it is a dataclass (using @dataclass decorator)
And it has a "trigger" field of type str
And it has a "source" field of type AgentState
And it has a "target" field of type AgentState
And it has an optional "guard" field that can be a callable or None
And it has an optional "action" field that can be a callable or None
```

### StateTransition records historical transitions for debugging

Researchers need to trace why cascades formed. Without transition history, debugging agent behavior at scale becomes impossible.

```
Given the prism/statechart/transitions.py file
When examining the StateTransition class
Then it is a dataclass
And it has a "from_state" field of type AgentState
And it has a "to_state" field of type AgentState
And it has a "trigger" field of type str
And it has a "timestamp" field of type datetime
And it has an optional "context" field that can be a dict or None
```

## Statechart Engine

### Statechart class manages states and transitions

The core engine must hold state definitions and transition rules. Without this centralized management, transition logic would be scattered and unmaintainable.

```
Given the prism/statechart/statechart.py file
When examining the Statechart class
Then it has an __init__ method that accepts states, transitions, and initial parameters
And it has a "states" attribute that holds the set of valid states
And it has a "transitions" attribute that holds the list of transitions
And it has an "initial" attribute for the starting state
```

### Statechart.fire() attempts state transitions

Agents need a single method to attempt state changes. Without fire(), the simulation loop would need to manually manage transition matching and guard evaluation.

```
Given the prism/statechart/statechart.py file
When examining the Statechart class
Then it has a fire method
And fire accepts agent, trigger, and optional context parameters
And fire returns an AgentState or None
```

### Statechart provides trigger introspection

The simulation loop needs to know what triggers are valid from a given state. Without valid_triggers(), the simulation cannot offer valid options to agents.

```
Given the prism/statechart/statechart.py file
When examining the Statechart class
Then it has a valid_triggers method that accepts a state parameter
And valid_triggers returns a list of trigger strings
```

### Statechart evaluates guards with fail-safe behavior

Guards may raise exceptions due to missing data or type errors. Per SCXML spec, failed guards must be treated as False to prevent simulation crashes.

```
Given the prism/statechart/statechart.py file
When examining the fire method implementation
Then guard evaluation is wrapped in try/except
And exceptions in guard evaluation result in the guard being treated as False
```

## LLM Reasoner

### StatechartReasoner decides ambiguous transitions via LLM

When multiple target states are valid, the LLM must decide based on agent personality and post context. Without the reasoner, ambiguous transitions would be resolved arbitrarily.

```
Given the prism/statechart/reasoner.py file
When examining the StatechartReasoner class
Then it has an __init__ that accepts an LLM client
And it has an async decide method
And decide accepts agent, current_state, trigger, options, and context parameters
And decide returns an AgentState
```

### Reasoner prompt includes agent profile and context

The LLM needs sufficient context to make personality-consistent decisions. Without agent interests and post content in the prompt, decisions would be random rather than character-driven.

```
Given the prism/statechart/reasoner.py file
When examining the prompt building logic
Then the prompt includes the agent's name or identifier
And the prompt includes the agent's interests
And the prompt includes the available state options
And the prompt requests JSON output with a next_state field
```

### Reasoner handles parse errors with fallback

LLM responses may be malformed. Without graceful fallback, parse errors would crash the simulation or leave agents in undefined states.

```
Given the prism/statechart/reasoner.py file
When examining the decide method implementation
Then there is error handling for JSON parse failures
And on parse error, it returns a fallback state (first option or SCROLLING)
```

## State Queries

### agents_in_state counts agents in a specific state

Researchers need real-time state distribution for analysis. Without this query function, counting would require manual iteration throughout the codebase.

```
Given the prism/statechart/queries.py file
When examining the agents_in_state function
Then it accepts a state parameter and an agents list parameter
And it returns an integer count
```

### state_distribution returns counts for all states

Researchers need the full state distribution at any simulation round. Without this function, building histograms and visualizations would require manual aggregation.

```
Given the prism/statechart/queries.py file
When examining the state_distribution function
Then it accepts an agents list parameter
And it returns a dictionary mapping AgentState to integer counts
```

## SocialAgent Integration

### SocialAgent has state tracking fields

Agents must track their current state and history. Without these fields, the statechart integration has no place to store agent-specific state.

```
Given the prism/agents/social_agent.py file
When examining the SocialAgent class
Then it has a "state" field or attribute of type AgentState
And it has a "state_history" field or attribute that is a list
And it has a "ticks_in_state" field or attribute that is an integer
```

### SocialAgent tracks behavioral thresholds

Different agent archetypes need different engagement thresholds. Without parameterized thresholds, all agents would behave identically in guard evaluation.

```
Given the prism/agents/social_agent.py file
When examining the SocialAgent class
Then it has an "engagement_threshold" field or parameter (float)
And it has a "timeout_threshold" field or parameter (int)
```

### SocialAgent provides state transition method

State changes must be atomic and record history. Without a dedicated method, transition logic would be scattered and history recording might be forgotten.

```
Given the prism/agents/social_agent.py file
When examining the SocialAgent class
Then it has a transition_to method or equivalent
And the method records the transition in state_history
And the method resets ticks_in_state to 0
```

### SocialAgent supports timeout detection

Stuck agents need automatic recovery. Without timeout detection, agents could deadlock indefinitely in certain states.

```
Given the prism/agents/social_agent.py file
When examining the SocialAgent class
Then it has a method to increment ticks_in_state (tick or similar)
And it has a method to check timeout status (is_timed_out or similar)
```
