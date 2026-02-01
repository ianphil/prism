"""Trigger determination for statechart transitions.

This module provides the determine_trigger function that maps agent state
and context to the appropriate trigger name for statechart transitions.
"""

from typing import Any

from prism.rag.models import Post
from prism.simulation.state import SimulationState
from prism.statechart.states import AgentState


def determine_trigger(
    agent: Any,
    feed: list[Post],
    state: SimulationState | None,
) -> str:
    """Determine the appropriate trigger for an agent based on state and context.

    Maps the agent's current state and context (feed contents, simulation state)
    to the trigger name that should be fired on the statechart.

    Args:
        agent: The agent to determine trigger for (must have .state attribute).
        feed: List of posts in the agent's feed (may be empty).
        state: Current simulation state (may be None).

    Returns:
        A string trigger name for the statechart.
    """
    current_state = agent.state

    match current_state:
        case AgentState.IDLE:
            return "start_browsing"
        case AgentState.SCROLLING:
            if feed:
                return "sees_post"
            return "feed_empty"
        case AgentState.EVALUATING:
            return "decides"
        case AgentState.COMPOSING:
            return "finishes_composing"
        case (
            AgentState.ENGAGING_LIKE
            | AgentState.ENGAGING_REPLY
            | AgentState.ENGAGING_RESHARE
        ):
            return "finishes_engaging"
        case AgentState.RESTING:
            return "rested"
        case _:
            return "start_browsing"
