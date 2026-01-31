---
target:
  - prism/simulation/config.py
  - prism/simulation/state.py
  - prism/simulation/controller.py
  - prism/simulation/executors/decision.py
  - prism/simulation/triggers.py
  - prism/simulation/statechart_factory.py
  - prism/simulation/checkpointer.py
---

# Simulation Workflow Loop Spec Tests

These tests verify the simulation orchestration layer that connects PRISM's components into a working round-based simulation.

## Configuration

### SimulationConfig Validates Bounds

Researchers need clear error messages when they misconfigure simulations. Invalid configs waste compute time and produce confusing failures. The config must reject invalid values early with actionable errors.

```
Given the prism/simulation/config.py file
When examining the SimulationConfig class
Then max_rounds has a validator requiring >= 1
And checkpoint_frequency has a validator requiring >= 1
And all fields have sensible defaults that allow minimal configuration
```

### Config Loads From YAML Section

Researchers configure simulations via YAML files, not code changes. The config must load from a `simulation:` section in the YAML, allowing defaults for unspecified fields so minimal configs work.

```
Given the prism/simulation/config.py file
When examining how configuration is loaded
Then there is a function or method to load SimulationConfig from a dict
And missing optional fields use default values
And Path fields can be parsed from strings
```

## Simulation State

### SimulationState Contains Required Components

The simulation state is the single source of truth during execution. It must hold posts, agents, the statechart, and metrics so executors have everything they need without external dependencies.

```
Given the prism/simulation/state.py file
When examining the SimulationState class
Then it has a posts field of type list[Post]
And it has an agents field of type list[SocialAgent] or list with agent type hint
And it has a round_number field of type int
And it has a metrics field of type EngagementMetrics
And it has a statechart field of type Statechart
```

### SimulationState Validates Agent Requirement

A simulation without agents is meaningless and would cause cryptic errors later. Validating at state construction gives clear feedback about what's wrong.

```
Given the prism/simulation/state.py file
When examining the SimulationState class validation
Then there is a validator that raises ValueError if agents list is empty
```

### EngagementMetrics Tracks Cumulative Engagement

Researchers analyze engagement patterns across the simulation. Metrics must track cumulative likes, reshares, replies, and posts created to compute rates and totals.

```
Given the prism/simulation/state.py file
When examining the EngagementMetrics class
Then it has total_likes, total_reshares, total_replies, and posts_created fields
And all fields default to 0
And all fields have ge=0 constraint or equivalent validation
```

### State Distribution Available From SimulationState

Per-round state distribution is critical for observability and research analysis. The state must expose this without requiring external calls, leveraging the existing state_distribution() function.

```
Given the prism/simulation/state.py file
When examining the SimulationState class
Then it has a method get_state_distribution that returns dict[AgentState, int]
And this method uses or delegates to the existing state_distribution function from prism.statechart.queries
```

## Trigger Determination

### Determine Trigger Maps State to Event

The statechart fires on triggers, but agents exist in states with context. The trigger determination logic bridges this gap, mapping agent state + context to the appropriate trigger name. Without this, the statechart cannot operate.

```
Given the prism/simulation/triggers.py file
When examining the determine_trigger function
Then it takes agent, feed, and state as parameters
And it returns a string trigger name
And it handles at least IDLE, SCROLLING, EVALUATING states with different triggers
And it uses match/case or if/elif for state-based dispatch
```

### Trigger Handles Timeout State

Agents stuck in a state too long need recovery. The trigger logic must check for timeout and return a timeout trigger that the statechart can use to force recovery.

```
Given the prism/simulation/triggers.py file
When examining timeout handling
Then there is logic that returns "timeout" trigger when agent.is_timed_out() is True
Or the trigger determination is called after timeout check at the executor level
```

## Statechart Factory

### Factory Creates Social Media Statechart

A standard statechart definition encodes the social media browsing behavior model. The factory function creates this shared definition that all agents use, ensuring consistent state machine semantics.

```
Given the prism/simulation/statechart_factory.py file
When examining the create_social_media_statechart function
Then it returns a Statechart instance
And the statechart includes states from AgentState (at minimum IDLE, SCROLLING, EVALUATING)
And the statechart includes transitions with triggers like "start_browsing", "sees_post", or "decides"
```

### Statechart Has Initial State

Every statechart needs an initial state for new agents. The factory must specify this so agents start in a well-defined state.

```
Given the prism/simulation/statechart_factory.py file
When examining the create_social_media_statechart function
Then the returned Statechart has an initial state set
And the initial state is AgentState.IDLE or AgentState.SCROLLING
```

## Decision Executor

### Decision Executor Uses Statechart Fire

The decision executor is the heart of statechart integration. It must call statechart.fire() to determine transitions, not bypass it with direct state manipulation. This ensures guards and actions are properly evaluated.

```
Given the prism/simulation/executors/decision.py file
When examining the AgentDecisionExecutor class
Then its execute method calls statechart.fire() with trigger, current_state, agent, and context
And it handles the case where fire() returns None (no valid transition)
```

### Decision Executor Invokes Reasoner For Ambiguous Cases

When multiple transitions are valid, the LLM reasoner decides. The executor must detect ambiguous cases (multiple valid targets) and delegate to the reasoner.

```
Given the prism/simulation/executors/decision.py file
When examining the AgentDecisionExecutor class
Then there is logic to check for multiple valid targets using statechart.valid_targets()
And if multiple targets exist and reasoner is available, reasoner.decide() is called
And the reasoner result is used as the new state
```

### Decision Executor Transitions Agent

After determining the new state, the executor must call agent.transition_to() to record the state change in history and reset the tick counter. This maintains proper state tracking.

```
Given the prism/simulation/executors/decision.py file
When examining the AgentDecisionExecutor class
Then agent.transition_to() is called with the new state and trigger
And this happens after fire() or reasoner.decide() determines the target state
```

### Decision Executor Returns Structured Result

The pipeline needs structured decision results to update state and log properly. The executor must return a DecisionResult with all required fields.

```
Given the prism/simulation/executors/decision.py file
When examining the AgentDecisionExecutor class
Then the execute method returns a DecisionResult or equivalent structured type
And the result includes agent_id, trigger, from_state, and to_state
```

## Round Controller

### Controller Iterates Rounds

Researchers configure simulation length via max_rounds. The controller must iterate exactly that many rounds, processing all agents each round.

```
Given the prism/simulation/controller.py file
When examining the RoundController class
Then there is a run_simulation or equivalent method that accepts config
And it iterates for config.max_rounds rounds
And it processes all agents each round
```

### Controller Supports Checkpointing

Long simulations need checkpoint recovery. The controller must save checkpoints at the configured frequency so researchers can resume from failures.

```
Given the prism/simulation/controller.py file
When examining the RoundController class
Then there is logic to save checkpoints based on checkpoint_frequency
And checkpoints are saved using a Checkpointer or equivalent
And checkpoint saving can be disabled (when checkpoint_dir is None)
```

### Controller Returns Final Result

After simulation completes, researchers need summary metrics. The controller must return a SimulationResult or equivalent with total_rounds and final metrics.

```
Given the prism/simulation/controller.py file
When examining the RoundController class
Then run_simulation returns a SimulationResult or dict with final metrics
And the result includes total_rounds and final engagement metrics
```

## Checkpointing

### Checkpointer Saves State To JSON

Human-readable checkpoints aid debugging and analysis. The checkpointer must serialize state to JSON with proper structure.

```
Given the prism/simulation/checkpointer.py file
When examining the Checkpointer class
Then there is a save method that takes SimulationState
And it writes JSON to a file
And the file path includes the round number
```

### Checkpointer Loads State From JSON

Resume functionality requires loading saved state. The checkpointer must deserialize JSON back to SimulationState, reconstructing posts and agent state.

```
Given the prism/simulation/checkpointer.py file
When examining the Checkpointer class
Then there is a load method that takes a Path
And it returns a SimulationState or components needed to reconstruct one
And it validates the checkpoint version
```

### Checkpoint Includes Version Field

Checkpoint format may evolve. The version field enables graceful handling of format changes and clear errors for incompatible checkpoints.

```
Given the prism/simulation/checkpointer.py file
When examining checkpoint serialization
Then saved checkpoints include a "version" field
And the load method checks the version and raises ValueError for unsupported versions
```

### Checkpointer Uses Atomic Write

Interrupted writes corrupt checkpoints. Atomic write (temp file + rename) prevents corruption, ensuring checkpoints are always complete.

```
Given the prism/simulation/checkpointer.py file
When examining the save method
Then it writes to a temporary file first
And it renames the temp file to the final path
Or uses another atomic write pattern
```
