"""Protocol definitions for simulation type safety.

This module defines Protocol classes that describe the minimal interfaces
expected by simulation components. Using protocols enables structural
subtyping - any class with matching attributes/methods satisfies the protocol.
"""

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from prism.statechart.states import AgentState


class SocialAgentProtocol(Protocol):
    """Minimal interface for agents in simulation.

    Any class with these attributes and methods can be used as an agent
    in the simulation, regardless of its actual type or inheritance.

    Attributes:
        agent_id: Unique identifier for the agent.
        name: Display name of the agent.
        interests: List of topics the agent is interested in.
        personality: Description of agent's personality traits.
        state: Current behavioral state in the statechart.
        ticks_in_state: Number of ticks spent in current state.
        engagement_threshold: Threshold for engagement decisions.
    """

    agent_id: str
    name: str
    interests: list[str]
    personality: str
    state: "AgentState"
    ticks_in_state: int
    engagement_threshold: float

    def tick(self) -> None:
        """Increment ticks_in_state counter."""
        ...

    def is_timed_out(self) -> bool:
        """Check if agent has exceeded time limit in current state."""
        ...

    def transition_to(
        self,
        new_state: "AgentState",
        trigger: str,
        context: dict | None = None,
    ) -> None:
        """Transition agent to a new state."""
        ...

    def should_engage(self, relevance: float) -> bool:
        """Decide whether to engage based on content relevance."""
        ...


class StatechartReasonerProtocol(Protocol):
    """Minimal interface for reasoner in simulation.

    The reasoner is used to resolve ambiguous state transitions when
    multiple valid target states exist.
    """

    async def decide(
        self,
        agent: SocialAgentProtocol,
        current_state: "AgentState",
        trigger: str,
        options: list["AgentState"],
        context: Any = None,
    ) -> "AgentState":
        """Decide which target state to transition to.

        Args:
            agent: The agent making the decision.
            current_state: Agent's current state.
            trigger: The trigger that caused the transition.
            options: List of valid target states to choose from.
            context: Additional context for the decision.

        Returns:
            The chosen target state.
        """
        ...
