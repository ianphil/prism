"""Agent behavioral states for statechart system.

This module defines the AgentState enum that represents all possible
behavioral states for social agents in the simulation.
"""

from enum import Enum


class AgentState(str, Enum):
    """Behavioral states for social agents.

    Inherits from str to enable direct JSON serialization without
    custom encoders. All values are lowercase strings.
    """

    IDLE = "idle"
    SCROLLING = "scrolling"
    EVALUATING = "evaluating"
    COMPOSING = "composing"
    ENGAGING_LIKE = "engaging_like"
    ENGAGING_REPLY = "engaging_reply"
    ENGAGING_RESHARE = "engaging_reshare"
    RESTING = "resting"
