"""Query functions for statechart state analysis.

This module provides utility functions for querying and analyzing
the state distribution of agents in a simulation.
"""

from typing import Any

from prism.statechart.states import AgentState


def agents_in_state(state: AgentState, agents: list[Any]) -> int:
    """Count agents that are in the specified state.

    Args:
        state: The AgentState to count
        agents: List of agent objects with a 'state' attribute

    Returns:
        Integer count of agents in the specified state
    """
    return sum(1 for agent in agents if agent.state == state)


def state_distribution(agents: list[Any]) -> dict[AgentState, int]:
    """Get distribution of agents across all states.

    Returns a dictionary mapping each AgentState to the count of agents
    currently in that state. All states are included, even those with
    zero agents.

    Args:
        agents: List of agent objects with a 'state' attribute

    Returns:
        Dictionary mapping AgentState to integer count
    """
    # Initialize all states with 0 count
    distribution: dict[AgentState, int] = {state: 0 for state in AgentState}

    # Count agents in each state
    for agent in agents:
        if agent.state in distribution:
            distribution[agent.state] += 1

    return distribution
