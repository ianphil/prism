"""Tests for AgentState enum (T001)."""

from enum import Enum


class TestAgentState:
    """Tests for the AgentState enum."""

    def test_agent_state_is_enum(self):
        """AgentState should be an Enum."""
        from prism.statechart.states import AgentState

        assert issubclass(AgentState, Enum)

    def test_agent_state_inherits_from_str(self):
        """AgentState should inherit from str for JSON serialization."""
        from prism.statechart.states import AgentState

        assert issubclass(AgentState, str)

    def test_idle_state_exists(self):
        """IDLE state should exist with lowercase value."""
        from prism.statechart.states import AgentState

        assert hasattr(AgentState, "IDLE")
        assert AgentState.IDLE.value == "idle"

    def test_scrolling_state_exists(self):
        """SCROLLING state should exist with lowercase value."""
        from prism.statechart.states import AgentState

        assert hasattr(AgentState, "SCROLLING")
        assert AgentState.SCROLLING.value == "scrolling"

    def test_evaluating_state_exists(self):
        """EVALUATING state should exist with lowercase value."""
        from prism.statechart.states import AgentState

        assert hasattr(AgentState, "EVALUATING")
        assert AgentState.EVALUATING.value == "evaluating"

    def test_composing_state_exists(self):
        """COMPOSING state should exist with lowercase value."""
        from prism.statechart.states import AgentState

        assert hasattr(AgentState, "COMPOSING")
        assert AgentState.COMPOSING.value == "composing"

    def test_engaging_like_state_exists(self):
        """ENGAGING_LIKE state should exist with lowercase value."""
        from prism.statechart.states import AgentState

        assert hasattr(AgentState, "ENGAGING_LIKE")
        assert AgentState.ENGAGING_LIKE.value == "engaging_like"

    def test_engaging_reply_state_exists(self):
        """ENGAGING_REPLY state should exist with lowercase value."""
        from prism.statechart.states import AgentState

        assert hasattr(AgentState, "ENGAGING_REPLY")
        assert AgentState.ENGAGING_REPLY.value == "engaging_reply"

    def test_engaging_reshare_state_exists(self):
        """ENGAGING_RESHARE state should exist with lowercase value."""
        from prism.statechart.states import AgentState

        assert hasattr(AgentState, "ENGAGING_RESHARE")
        assert AgentState.ENGAGING_RESHARE.value == "engaging_reshare"

    def test_resting_state_exists(self):
        """RESTING state should exist with lowercase value."""
        from prism.statechart.states import AgentState

        assert hasattr(AgentState, "RESTING")
        assert AgentState.RESTING.value == "resting"

    def test_agent_state_str_representation(self):
        """AgentState values should be usable as strings directly."""
        from prism.statechart.states import AgentState

        # Since AgentState inherits from str, it should be usable as a string
        assert AgentState.IDLE == "idle"
        assert AgentState.SCROLLING == "scrolling"

    def test_agent_state_json_serializable(self):
        """AgentState should be JSON serializable due to str inheritance."""
        import json

        from prism.statechart.states import AgentState

        # str-based enums serialize directly without custom encoder
        data = {"state": AgentState.IDLE}
        result = json.dumps(data)
        assert '"idle"' in result

    def test_all_states_have_lowercase_values(self):
        """All AgentState values should be lowercase strings."""
        from prism.statechart.states import AgentState

        for state in AgentState:
            assert state.value == state.value.lower()
            assert isinstance(state.value, str)
