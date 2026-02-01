"""Agent round executor for simulation pipeline.

This module provides the AgentRoundExecutor that coordinates the full
executor pipeline for one agent's turn in the simulation.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from prism.simulation.executors.decision import AgentDecisionExecutor
    from prism.simulation.executors.feed import FeedRetrievalExecutor
    from prism.simulation.executors.logging import LoggingExecutor
    from prism.simulation.executors.state_update import StateUpdateExecutor
    from prism.simulation.results import DecisionResult
    from prism.simulation.state import SimulationState


class AgentRoundExecutor:
    """Coordinates the full executor pipeline for one agent turn.

    The pipeline executes in order:
    1. Feed retrieval - get posts for agent
    2. Agent decision - statechart-driven decision
    3. State update - apply action to state
    4. Logging - record decision to log
    """

    def __init__(
        self,
        feed_executor: "FeedRetrievalExecutor",
        decision_executor: "AgentDecisionExecutor",
        state_executor: "StateUpdateExecutor",
        logging_executor: "LoggingExecutor | None" = None,
    ) -> None:
        """Initialize with all pipeline executors.

        Args:
            feed_executor: Executor for feed retrieval.
            decision_executor: Executor for agent decisions.
            state_executor: Executor for state updates.
            logging_executor: Executor for decision logging (optional).
        """
        self._feed = feed_executor
        self._decision = decision_executor
        self._state = state_executor
        self._logging = logging_executor

    async def execute(
        self,
        agent: Any,
        state: "SimulationState",
    ) -> "DecisionResult":
        """Execute full pipeline for one agent.

        Args:
            agent: The agent taking their turn.
            state: Current simulation state.

        Returns:
            DecisionResult from the agent's turn.
        """
        # 1. Feed retrieval
        feed = await self._feed.execute_async(agent=agent, state=state)

        # 2. Agent decision
        decision = await self._decision.execute(agent=agent, state=state, feed=feed)

        # 3. State update
        await self._state.execute(agent=agent, state=state, decision=decision)

        # 4. Logging (only if executor provided)
        if self._logging is not None:
            await self._logging.execute(agent=agent, state=state, decision=decision)

        return decision
