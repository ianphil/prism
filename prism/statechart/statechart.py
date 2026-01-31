"""Statechart engine for agent behavior.

This module provides the core Statechart class that manages state transitions
for agents based on triggers and guards.
"""

from typing import Any

from prism.statechart.states import AgentState
from prism.statechart.transitions import Transition


class Statechart:
    """A statechart engine that manages state transitions.

    The Statechart validates its configuration at construction time and
    provides methods for firing transitions and introspecting valid triggers.

    Attributes:
        states: Set of valid states for this statechart
        transitions: List of transitions defining state changes
        initial: The initial state for new instances
    """

    def __init__(
        self,
        states: set[AgentState],
        transitions: list[Transition],
        initial: AgentState,
    ) -> None:
        """Initialize the statechart with states, transitions, and initial state.

        Args:
            states: Set of valid AgentState values for this statechart
            transitions: List of Transition objects defining valid state changes
            initial: The initial state (must be in states)

        Raises:
            ValueError: If initial is not in states, or if any transition
                        has source/target not in states
        """
        # Validate initial state
        if initial not in states:
            raise ValueError(f"initial state {initial} not in states")

        # Validate all transition sources and targets
        for transition in transitions:
            if transition.source not in states:
                raise ValueError(f"transition source {transition.source} not in states")
            if transition.target not in states:
                raise ValueError(f"transition target {transition.target} not in states")

        self.states = states
        self.transitions = transitions
        self.initial = initial

    def fire(
        self,
        trigger: str,
        current_state: AgentState,
        agent: Any,
        context: dict | None,
    ) -> AgentState | None:
        """Attempt to fire a transition based on trigger and current state.

        Evaluates transitions in definition order. The first transition whose
        trigger and source match, and whose guard (if any) returns True, will
        fire.

        Args:
            trigger: The event trigger name
            current_state: The agent's current state
            agent: The agent object (passed to guards)
            context: Optional context dict (passed to guards)

        Returns:
            The target state if a transition fires, None otherwise
        """
        for transition in self.transitions:
            # Check if trigger and source match
            if transition.trigger != trigger:
                continue
            if transition.source != current_state:
                continue

            # Evaluate guard if present (fail-safe: exceptions treated as False)
            if transition.guard is not None:
                try:
                    guard_result = transition.guard(agent, context)
                    # Coerce non-boolean to bool
                    if not bool(guard_result):
                        continue
                except Exception:
                    # Guard exception treated as False - continue to next transition
                    continue

            # Transition matches - return target state
            return transition.target

        # No matching transition found
        return None

    def valid_triggers(self, state: AgentState) -> list[str]:
        """Get list of triggers available from a given state.

        Returns unique trigger names for all transitions originating from the
        given state, preserving definition order for the first occurrence of
        each trigger.

        Args:
            state: The source state to check triggers for

        Returns:
            List of unique trigger names available from this state
        """
        seen: set[str] = set()
        triggers: list[str] = []

        for transition in self.transitions:
            if transition.source == state and transition.trigger not in seen:
                seen.add(transition.trigger)
                triggers.append(transition.trigger)

        return triggers

    def valid_targets(self, state: AgentState, trigger: str) -> list[AgentState]:
        """Get list of possible target states for a trigger from a given state.

        Returns all target states that could be reached from the given state
        using the given trigger, regardless of guards.

        Args:
            state: The source state
            trigger: The trigger name

        Returns:
            List of possible target states (may contain duplicates if multiple
            transitions have the same target)
        """
        targets: list[AgentState] = []

        for transition in self.transitions:
            if transition.source == state and transition.trigger == trigger:
                targets.append(transition.target)

        return targets
