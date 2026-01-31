"""Tests for Transition and StateTransition dataclasses (T003, T005)."""

from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import datetime
from typing import get_type_hints

import pytest

from prism.statechart.states import AgentState


class TestTransition:
    """Tests for the Transition dataclass (T003)."""

    def test_transition_is_dataclass(self):
        """Transition should be a dataclass."""
        from prism.statechart.transitions import Transition

        assert is_dataclass(Transition)

    def test_transition_has_trigger_field(self):
        """Transition should have a trigger field of type str."""
        from prism.statechart.transitions import Transition

        field_names = {f.name for f in fields(Transition)}
        assert "trigger" in field_names

        hints = get_type_hints(Transition)
        assert hints["trigger"] is str

    def test_transition_has_source_field(self):
        """Transition should have a source field of type AgentState."""
        from prism.statechart.transitions import Transition

        field_names = {f.name for f in fields(Transition)}
        assert "source" in field_names

        hints = get_type_hints(Transition)
        assert hints["source"] == AgentState

    def test_transition_has_target_field(self):
        """Transition should have a target field of type AgentState."""
        from prism.statechart.transitions import Transition

        field_names = {f.name for f in fields(Transition)}
        assert "target" in field_names

        hints = get_type_hints(Transition)
        assert hints["target"] == AgentState

    def test_transition_has_optional_guard_field(self):
        """Transition should have an optional guard field (callable or None)."""
        from prism.statechart.transitions import Transition

        field_names = {f.name for f in fields(Transition)}
        assert "guard" in field_names

        # Guard should default to None
        t = Transition(
            trigger="test", source=AgentState.IDLE, target=AgentState.SCROLLING
        )
        assert t.guard is None

    def test_transition_has_optional_action_field(self):
        """Transition should have an optional action field (callable or None)."""
        from prism.statechart.transitions import Transition

        field_names = {f.name for f in fields(Transition)}
        assert "action" in field_names

        # Action should default to None
        t = Transition(
            trigger="test", source=AgentState.IDLE, target=AgentState.SCROLLING
        )
        assert t.action is None

    def test_transition_is_frozen(self):
        """Transition should be immutable (frozen)."""
        from prism.statechart.transitions import Transition

        t = Transition(
            trigger="test", source=AgentState.IDLE, target=AgentState.SCROLLING
        )

        with pytest.raises(FrozenInstanceError):
            t.trigger = "modified"

    def test_transition_with_guard_callable(self):
        """Transition should accept a callable as guard."""
        from prism.statechart.transitions import Transition

        def my_guard(agent, context):
            return True

        t = Transition(
            trigger="test",
            source=AgentState.IDLE,
            target=AgentState.SCROLLING,
            guard=my_guard,
        )
        assert t.guard is my_guard
        assert t.guard(None, None) is True

    def test_transition_with_action_callable(self):
        """Transition should accept a callable as action."""
        from prism.statechart.transitions import Transition

        def my_action(agent, context):
            pass

        t = Transition(
            trigger="test",
            source=AgentState.IDLE,
            target=AgentState.SCROLLING,
            action=my_action,
        )
        assert t.action is my_action

    def test_transition_creation_with_all_fields(self):
        """Transition should be creatable with all fields specified."""
        from prism.statechart.transitions import Transition

        def guard(a, c):
            return True

        def action(a, c):
            pass

        t = Transition(
            trigger="evaluate",
            source=AgentState.SCROLLING,
            target=AgentState.EVALUATING,
            guard=guard,
            action=action,
        )

        assert t.trigger == "evaluate"
        assert t.source == AgentState.SCROLLING
        assert t.target == AgentState.EVALUATING
        assert t.guard is guard
        assert t.action is action


class TestStateTransition:
    """Tests for the StateTransition dataclass (T005)."""

    def test_state_transition_is_dataclass(self):
        """StateTransition should be a dataclass."""
        from prism.statechart.transitions import StateTransition

        assert is_dataclass(StateTransition)

    def test_state_transition_has_from_state_field(self):
        """StateTransition should have a from_state field of type AgentState."""
        from prism.statechart.transitions import StateTransition

        field_names = {f.name for f in fields(StateTransition)}
        assert "from_state" in field_names

        hints = get_type_hints(StateTransition)
        assert hints["from_state"] == AgentState

    def test_state_transition_has_to_state_field(self):
        """StateTransition should have a to_state field of type AgentState."""
        from prism.statechart.transitions import StateTransition

        field_names = {f.name for f in fields(StateTransition)}
        assert "to_state" in field_names

        hints = get_type_hints(StateTransition)
        assert hints["to_state"] == AgentState

    def test_state_transition_has_trigger_field(self):
        """StateTransition should have a trigger field of type str."""
        from prism.statechart.transitions import StateTransition

        field_names = {f.name for f in fields(StateTransition)}
        assert "trigger" in field_names

        hints = get_type_hints(StateTransition)
        assert hints["trigger"] is str

    def test_state_transition_has_timestamp_field(self):
        """StateTransition should have a timestamp field of type datetime."""
        from prism.statechart.transitions import StateTransition

        field_names = {f.name for f in fields(StateTransition)}
        assert "timestamp" in field_names

        hints = get_type_hints(StateTransition)
        assert hints["timestamp"] == datetime

    def test_state_transition_has_optional_context_field(self):
        """StateTransition should have an optional context field (dict or None)."""
        from prism.statechart.transitions import StateTransition

        field_names = {f.name for f in fields(StateTransition)}
        assert "context" in field_names

        # Context should default to None
        now = datetime.now()
        st = StateTransition(
            from_state=AgentState.IDLE,
            to_state=AgentState.SCROLLING,
            trigger="start",
            timestamp=now,
        )
        assert st.context is None

    def test_state_transition_with_context(self):
        """StateTransition should accept a dict as context."""
        from prism.statechart.transitions import StateTransition

        now = datetime.now()
        context = {"post_id": "123", "relevance": 0.8}
        st = StateTransition(
            from_state=AgentState.SCROLLING,
            to_state=AgentState.EVALUATING,
            trigger="see_post",
            timestamp=now,
            context=context,
        )
        assert st.context == context
        assert st.context["post_id"] == "123"

    def test_state_transition_creation_with_all_fields(self):
        """StateTransition should be creatable with all fields specified."""
        from prism.statechart.transitions import StateTransition

        now = datetime.now()
        context = {"reason": "interesting content"}

        st = StateTransition(
            from_state=AgentState.EVALUATING,
            to_state=AgentState.ENGAGING_LIKE,
            trigger="decide_engage",
            timestamp=now,
            context=context,
        )

        assert st.from_state == AgentState.EVALUATING
        assert st.to_state == AgentState.ENGAGING_LIKE
        assert st.trigger == "decide_engage"
        assert st.timestamp == now
        assert st.context == context

    def test_state_transition_timestamp_is_datetime(self):
        """StateTransition timestamp should be a datetime object."""
        from prism.statechart.transitions import StateTransition

        now = datetime.now()
        st = StateTransition(
            from_state=AgentState.IDLE,
            to_state=AgentState.SCROLLING,
            trigger="start",
            timestamp=now,
        )
        assert isinstance(st.timestamp, datetime)
