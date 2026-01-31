# Contract: Executor Protocol

## Purpose

Defines the async executor protocol and interfaces for the simulation pipeline.

## Base Protocol

```python
from typing import Protocol, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from prism.agents.social_agent import SocialAgent
    from prism.simulation.state import SimulationState


class Executor(Protocol):
    """Protocol for simulation executors.

    All executors are async and receive the agent and simulation state.
    Return types vary by executor.
    """

    async def execute(
        self,
        agent: "SocialAgent",
        state: "SimulationState",
        **kwargs: Any,
    ) -> Any:
        """Execute this step of the pipeline."""
        ...
```

## FeedRetrievalExecutor

```python
from prism.rag.models import Post
from prism.rag.retriever import FeedRetriever


class FeedRetrievalExecutor:
    """Retrieves feed posts for an agent.

    Wraps FeedRetriever.get_feed() in the executor interface.
    """

    def __init__(self, retriever: FeedRetriever) -> None:
        self._retriever = retriever

    async def execute(
        self,
        agent: "SocialAgent",
        state: "SimulationState",
    ) -> list[Post]:
        """Retrieve feed for the agent based on their interests.

        Returns:
            List of Post objects (up to feed_size).
        """
        return self._retriever.get_feed(interests=agent.interests)
```

## AgentDecisionExecutor

```python
from prism.simulation.state import DecisionResult, ActionResult
from prism.simulation.triggers import determine_trigger
from prism.statechart.states import AgentState


class AgentDecisionExecutor:
    """Executes statechart-driven agent decisions.

    Handles the full decision flow:
    1. Tick agent time-in-state
    2. Determine trigger from context
    3. Fire statechart transition
    4. Invoke reasoner if ambiguous
    5. Transition agent to new state
    6. Execute action based on new state
    """

    async def execute(
        self,
        agent: "SocialAgent",
        state: "SimulationState",
        feed: list[Post],
    ) -> DecisionResult:
        """Execute decision logic for one agent turn.

        Args:
            agent: The agent making the decision
            state: Current simulation state
            feed: Feed posts retrieved for this agent

        Returns:
            DecisionResult with state transition and action details
        """
        # 1. Tick time-in-state
        agent.tick()

        # 2. Determine trigger
        if agent.is_timed_out():
            trigger = "timeout"
        else:
            trigger = determine_trigger(agent, feed, state)

        from_state = agent.state

        # 3. Fire statechart transition
        new_state = state.statechart.fire(
            trigger=trigger,
            current_state=agent.state,
            agent=agent,
            context={"feed": feed, "state": state},
        )

        reasoner_used = False

        # 4. Handle ambiguous transitions
        if new_state is None and state.reasoner is not None:
            targets = state.statechart.valid_targets(agent.state, trigger)
            if len(targets) > 1:
                new_state = await state.reasoner.decide(
                    agent=agent,
                    current_state=agent.state,
                    trigger=trigger,
                    options=targets,
                    context={"feed": feed},
                )
                reasoner_used = True
            elif len(targets) == 1:
                new_state = targets[0]

        # 5. Transition agent
        if new_state is not None:
            agent.transition_to(new_state, trigger, context={"round": state.round_number})
        else:
            # No valid transition - stay in current state
            new_state = agent.state

        # 6. Execute action
        action = await self._execute_action(agent, new_state, feed, state)

        return DecisionResult(
            agent_id=agent.agent_id,
            trigger=trigger,
            from_state=from_state,
            to_state=new_state,
            action=action,
            reasoner_used=reasoner_used,
        )

    async def _execute_action(
        self,
        agent: "SocialAgent",
        new_state: AgentState,
        feed: list[Post],
        state: "SimulationState",
    ) -> ActionResult | None:
        """Execute action based on agent's new state."""
        match new_state:
            case AgentState.COMPOSING:
                # Agent composes new post (use LLM to generate content)
                return ActionResult(action_type="compose", new_post=...)

            case AgentState.ENGAGING_LIKE:
                # Agent likes current post
                target = feed[0] if feed else None
                return ActionResult(
                    action_type="like",
                    target_post_id=target.id if target else None,
                )

            case AgentState.ENGAGING_REPLY:
                # Agent replies to current post
                target = feed[0] if feed else None
                return ActionResult(
                    action_type="reply",
                    target_post_id=target.id if target else None,
                    new_post=...,  # Reply post
                    content=...,   # Reply content
                )

            case AgentState.ENGAGING_RESHARE:
                # Agent reshares current post
                target = feed[0] if feed else None
                return ActionResult(
                    action_type="reshare",
                    target_post_id=target.id if target else None,
                    new_post=...,  # Reshare post
                )

            case _:
                # SCROLLING, EVALUATING, IDLE, RESTING - no action
                return ActionResult(action_type="scroll")
```

## StateUpdateExecutor

```python
class StateUpdateExecutor:
    """Applies agent actions to simulation state.

    Updates post engagement counts and adds new posts.
    """

    def __init__(self, retriever: FeedRetriever) -> None:
        """Initialize with retriever for indexing new posts."""
        self._retriever = retriever

    async def execute(
        self,
        agent: "SocialAgent",
        state: "SimulationState",
        decision: DecisionResult,
    ) -> None:
        """Apply decision action to simulation state.

        Mutates state in place.
        """
        action = decision.action
        if action is None:
            return

        match action.action_type:
            case "like":
                if action.target_post_id:
                    post = state.get_post_by_id(action.target_post_id)
                    if post:
                        post.likes += 1
                        state.metrics.increment_like()

            case "reply":
                if action.target_post_id:
                    post = state.get_post_by_id(action.target_post_id)
                    if post:
                        post.replies += 1
                        state.metrics.increment_reply()
                if action.new_post:
                    state.add_post(action.new_post)
                    self._retriever.add_post(action.new_post)

            case "reshare":
                if action.target_post_id:
                    post = state.get_post_by_id(action.target_post_id)
                    if post:
                        post.reshares += 1
                        state.metrics.increment_reshare()
                if action.new_post:
                    state.add_post(action.new_post)
                    self._retriever.add_post(action.new_post)

            case "compose":
                if action.new_post:
                    state.add_post(action.new_post)
                    self._retriever.add_post(action.new_post)

            case "scroll":
                pass  # No state changes
```

## LoggingExecutor

```python
import json
import logging
from datetime import datetime, timezone


class LoggingExecutor:
    """Logs agent decisions to structured JSON.

    Writes to Python logger and optionally to a JSON lines file.
    """

    def __init__(
        self,
        logger: logging.Logger | None = None,
        log_file: Path | None = None,
    ) -> None:
        self._logger = logger or logging.getLogger("prism.simulation.decisions")
        self._log_file = log_file
        self._file_handle = None

        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            self._file_handle = open(log_file, "a")

    async def execute(
        self,
        agent: "SocialAgent",
        state: "SimulationState",
        decision: DecisionResult,
    ) -> None:
        """Log the decision to structured output."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "round": state.round_number,
            "agent_id": decision.agent_id,
            "trigger": decision.trigger,
            "from_state": decision.from_state.value,
            "to_state": decision.to_state.value,
            "action_type": decision.action.action_type if decision.action else None,
            "reasoner_used": decision.reasoner_used,
        }

        json_entry = json.dumps(entry)
        self._logger.info(json_entry)

        if self._file_handle:
            self._file_handle.write(json_entry + "\n")
            self._file_handle.flush()

    def close(self) -> None:
        """Close file handle if open."""
        if self._file_handle:
            self._file_handle.close()
```

## AgentRoundExecutor

```python
class AgentRoundExecutor:
    """Coordinates the full executor pipeline for one agent turn."""

    def __init__(
        self,
        feed_executor: FeedRetrievalExecutor,
        decision_executor: AgentDecisionExecutor,
        state_executor: StateUpdateExecutor,
        logging_executor: LoggingExecutor,
    ) -> None:
        self._feed = feed_executor
        self._decision = decision_executor
        self._state = state_executor
        self._logging = logging_executor

    async def execute(
        self,
        agent: "SocialAgent",
        state: "SimulationState",
    ) -> DecisionResult:
        """Execute full pipeline for one agent.

        Returns:
            DecisionResult from the agent's turn
        """
        # 1. Feed retrieval
        feed = await self._feed.execute(agent, state)

        # 2. Agent decision
        decision = await self._decision.execute(agent, state, feed)

        # 3. State update
        await self._state.execute(agent, state, decision)

        # 4. Logging
        await self._logging.execute(agent, state, decision)

        return decision
```

## Usage Example

```python
# Setup executors
feed_exec = FeedRetrievalExecutor(retriever)
decision_exec = AgentDecisionExecutor()
state_exec = StateUpdateExecutor(retriever)
logging_exec = LoggingExecutor(log_file=config.log_file)

round_executor = AgentRoundExecutor(
    feed_executor=feed_exec,
    decision_executor=decision_exec,
    state_executor=state_exec,
    logging_executor=logging_exec,
)

# Execute one agent's turn
result = await round_executor.execute(agent, state)
```
