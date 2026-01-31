"""Transition types for statechart system.

This module defines:
- Transition: Defines a state transition with optional guard and action
- StateTransition: Records a historical state transition for debugging
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

from prism.statechart.states import AgentState


@dataclass(frozen=True)
class Transition:
    """Defines a state transition with optional guard and action.

    Attributes:
        trigger: The event that triggers this transition
        source: The state from which this transition originates
        target: The state to which this transition leads
        guard: Optional callable (agent, context) -> bool that must return True
               for the transition to fire. Defaults to None (always fires).
        action: Optional callable (agent, context) -> None executed when
               the transition fires. Defaults to None.
    """

    trigger: str
    source: AgentState
    target: AgentState
    guard: Callable[[Any, dict | None], bool] | None = None
    action: Callable[[Any, dict | None], None] | None = None


@dataclass
class StateTransition:
    """Records a historical state transition for debugging and analysis.

    Attributes:
        from_state: The state the agent was in before the transition
        to_state: The state the agent moved to after the transition
        trigger: The event that triggered this transition
        timestamp: When the transition occurred
        context: Optional dict of additional context (post_id, relevance, etc.)
    """

    from_state: AgentState
    to_state: AgentState
    trigger: str
    timestamp: datetime
    context: dict | None = field(default=None)
