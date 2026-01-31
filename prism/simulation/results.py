"""Result types for simulation execution.

This module defines dataclasses for structured results from the
simulation pipeline including actions, decisions, rounds, and
final simulation results.
"""

from dataclasses import dataclass, field

from prism.simulation.state import EngagementMetrics
from prism.statechart.states import AgentState


@dataclass
class ActionResult:
    """Result of an action taken by an agent.

    Attributes:
        action: The type of action (like, reply, reshare, compose, scroll).
        target_post_id: ID of the post acted upon (None for compose).
        content: Optional content for reply or compose actions.
    """

    action: str
    target_post_id: str | None
    content: str | None = None


@dataclass
class DecisionResult:
    """Result of an agent's decision and state transition.

    Attributes:
        agent_id: ID of the agent that made the decision.
        trigger: The trigger that caused the transition.
        from_state: The agent's state before transition.
        to_state: The agent's state after transition.
        action: Optional action result if an action was taken.
    """

    agent_id: str
    trigger: str
    from_state: AgentState
    to_state: AgentState
    action: ActionResult | None = None


@dataclass
class RoundResult:
    """Result of a single simulation round.

    Attributes:
        round_number: The round number (0-indexed).
        decisions: List of decisions made by all agents this round.
    """

    round_number: int
    decisions: list[DecisionResult] = field(default_factory=list)


@dataclass
class SimulationResult:
    """Final result of a complete simulation.

    Attributes:
        total_rounds: Total number of rounds executed.
        final_metrics: Final engagement metrics at simulation end.
        rounds: List of results from each round.
    """

    total_rounds: int
    final_metrics: EngagementMetrics
    rounds: list[RoundResult] = field(default_factory=list)
