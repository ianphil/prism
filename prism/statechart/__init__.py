"""Agent behavior statecharts module.

This module provides the statechart system for managing agent behavioral states,
transitions, and queries.

Exports:
    AgentState: Enum of all possible agent behavioral states
    Transition: Defines state transitions with optional guards and actions
    StateTransition: Records historical state transitions for debugging
    Statechart: The statechart engine that manages state transitions
    StatechartReasoner: LLM-based reasoner for ambiguous transitions
    agents_in_state: Query function to count agents in a specific state
    state_distribution: Query function to get state distribution across agents
"""

from prism.statechart.queries import agents_in_state, state_distribution
from prism.statechart.reasoner import StatechartReasoner
from prism.statechart.statechart import Statechart
from prism.statechart.states import AgentState
from prism.statechart.transitions import StateTransition, Transition

__all__ = [
    "AgentState",
    "Transition",
    "StateTransition",
    "Statechart",
    "StatechartReasoner",
    "agents_in_state",
    "state_distribution",
]
