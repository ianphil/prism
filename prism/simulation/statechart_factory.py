"""Factory for creating social media behavior statecharts.

This module provides factory functions to create standard statechart
definitions for social media agent behavior.
"""

from prism.statechart.statechart import Statechart
from prism.statechart.states import AgentState
from prism.statechart.transitions import Transition


def create_social_media_statechart() -> Statechart:
    """Create the standard social media behavior statechart.

    This statechart defines the behavioral states and transitions for
    agents browsing and interacting with social media content.

    Returns:
        A Statechart instance configured for social media behavior.
    """
    states = set(AgentState)
    transitions: list[Transition] = [
        # IDLE -> SCROLLING on start_browsing
        Transition(
            trigger="start_browsing",
            source=AgentState.IDLE,
            target=AgentState.SCROLLING,
        ),
        # SCROLLING -> EVALUATING on sees_post
        Transition(
            trigger="sees_post",
            source=AgentState.SCROLLING,
            target=AgentState.EVALUATING,
        ),
        # SCROLLING -> RESTING on feed_empty
        Transition(
            trigger="feed_empty",
            source=AgentState.SCROLLING,
            target=AgentState.RESTING,
        ),
        # EVALUATING -> various states on decides
        Transition(
            trigger="decides",
            source=AgentState.EVALUATING,
            target=AgentState.COMPOSING,
        ),
        Transition(
            trigger="decides",
            source=AgentState.EVALUATING,
            target=AgentState.ENGAGING_LIKE,
        ),
        Transition(
            trigger="decides",
            source=AgentState.EVALUATING,
            target=AgentState.ENGAGING_REPLY,
        ),
        Transition(
            trigger="decides",
            source=AgentState.EVALUATING,
            target=AgentState.ENGAGING_RESHARE,
        ),
        Transition(
            trigger="decides",
            source=AgentState.EVALUATING,
            target=AgentState.SCROLLING,
        ),
        # COMPOSING -> SCROLLING on finishes_composing
        Transition(
            trigger="finishes_composing",
            source=AgentState.COMPOSING,
            target=AgentState.SCROLLING,
        ),
        # ENGAGING_* -> SCROLLING on finishes_engaging
        Transition(
            trigger="finishes_engaging",
            source=AgentState.ENGAGING_LIKE,
            target=AgentState.SCROLLING,
        ),
        Transition(
            trigger="finishes_engaging",
            source=AgentState.ENGAGING_REPLY,
            target=AgentState.SCROLLING,
        ),
        Transition(
            trigger="finishes_engaging",
            source=AgentState.ENGAGING_RESHARE,
            target=AgentState.SCROLLING,
        ),
        # RESTING -> IDLE on rested
        Transition(
            trigger="rested",
            source=AgentState.RESTING,
            target=AgentState.IDLE,
        ),
        # Timeout transitions from all non-IDLE states to IDLE
        Transition(
            trigger="timeout",
            source=AgentState.SCROLLING,
            target=AgentState.IDLE,
        ),
        Transition(
            trigger="timeout",
            source=AgentState.EVALUATING,
            target=AgentState.IDLE,
        ),
        Transition(
            trigger="timeout",
            source=AgentState.COMPOSING,
            target=AgentState.IDLE,
        ),
        Transition(
            trigger="timeout",
            source=AgentState.ENGAGING_LIKE,
            target=AgentState.IDLE,
        ),
        Transition(
            trigger="timeout",
            source=AgentState.ENGAGING_REPLY,
            target=AgentState.IDLE,
        ),
        Transition(
            trigger="timeout",
            source=AgentState.ENGAGING_RESHARE,
            target=AgentState.IDLE,
        ),
        Transition(
            trigger="timeout",
            source=AgentState.RESTING,
            target=AgentState.IDLE,
        ),
    ]

    return Statechart(
        states=states,
        transitions=transitions,
        initial=AgentState.IDLE,
    )
