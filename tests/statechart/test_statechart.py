"""Tests for Statechart class (T007-T015)."""

import pytest

from prism.statechart.states import AgentState
from prism.statechart.transitions import Transition


class TestStatechartInit:
    """Tests for Statechart.__init__() (T007)."""

    def test_statechart_accepts_states_transitions_initial(self):
        """Statechart should accept states set, transitions list, and initial state."""
        from prism.statechart.statechart import Statechart

        states = {AgentState.IDLE, AgentState.SCROLLING}
        transitions = [
            Transition(
                trigger="start", source=AgentState.IDLE, target=AgentState.SCROLLING
            )
        ]
        initial = AgentState.IDLE

        sc = Statechart(states=states, transitions=transitions, initial=initial)

        assert sc.states == states
        assert sc.transitions == transitions
        assert sc.initial == initial

    def test_statechart_validates_initial_in_states(self):
        """Statechart should raise ValueError if initial is not in states."""
        from prism.statechart.statechart import Statechart

        states = {AgentState.IDLE, AgentState.SCROLLING}
        transitions = []
        initial = AgentState.RESTING  # Not in states

        with pytest.raises(ValueError, match="initial.*not in states"):
            Statechart(states=states, transitions=transitions, initial=initial)

    def test_statechart_validates_transition_sources_in_states(self):
        """Statechart should raise ValueError if transition source is not in states."""
        from prism.statechart.statechart import Statechart

        states = {AgentState.IDLE, AgentState.SCROLLING}
        transitions = [
            Transition(
                trigger="invalid",
                source=AgentState.RESTING,  # Not in states
                target=AgentState.SCROLLING,
            )
        ]
        initial = AgentState.IDLE

        with pytest.raises(ValueError, match="source.*not in states"):
            Statechart(states=states, transitions=transitions, initial=initial)

    def test_statechart_validates_transition_targets_in_states(self):
        """Statechart should raise ValueError if transition target is not in states."""
        from prism.statechart.statechart import Statechart

        states = {AgentState.IDLE, AgentState.SCROLLING}
        transitions = [
            Transition(
                trigger="invalid",
                source=AgentState.IDLE,
                target=AgentState.RESTING,  # Not in states
            )
        ]
        initial = AgentState.IDLE

        with pytest.raises(ValueError, match="target.*not in states"):
            Statechart(states=states, transitions=transitions, initial=initial)

    def test_statechart_with_empty_transitions(self):
        """Statechart should accept empty transitions list."""
        from prism.statechart.statechart import Statechart

        states = {AgentState.IDLE}
        transitions = []
        initial = AgentState.IDLE

        sc = Statechart(states=states, transitions=transitions, initial=initial)
        assert sc.transitions == []

    def test_statechart_with_multiple_transitions(self):
        """Statechart should accept multiple transitions."""
        from prism.statechart.statechart import Statechart

        states = {AgentState.IDLE, AgentState.SCROLLING, AgentState.EVALUATING}
        transitions = [
            Transition(
                trigger="start", source=AgentState.IDLE, target=AgentState.SCROLLING
            ),
            Transition(
                trigger="see_post",
                source=AgentState.SCROLLING,
                target=AgentState.EVALUATING,
            ),
            Transition(
                trigger="pass",
                source=AgentState.EVALUATING,
                target=AgentState.SCROLLING,
            ),
        ]
        initial = AgentState.IDLE

        sc = Statechart(states=states, transitions=transitions, initial=initial)
        assert len(sc.transitions) == 3


class TestStatechartFire:
    """Tests for Statechart.fire() (T009)."""

    def test_fire_returns_target_when_transition_matches(self):
        """fire() should return target state when transition matches."""
        from prism.statechart.statechart import Statechart

        states = {AgentState.IDLE, AgentState.SCROLLING}
        transitions = [
            Transition(
                trigger="start", source=AgentState.IDLE, target=AgentState.SCROLLING
            )
        ]
        sc = Statechart(states=states, transitions=transitions, initial=AgentState.IDLE)

        result = sc.fire(
            trigger="start", current_state=AgentState.IDLE, agent=None, context=None
        )
        assert result == AgentState.SCROLLING

    def test_fire_returns_none_when_no_transition_matches_trigger(self):
        """fire() should return None when no transition matches the trigger."""
        from prism.statechart.statechart import Statechart

        states = {AgentState.IDLE, AgentState.SCROLLING}
        transitions = [
            Transition(
                trigger="start", source=AgentState.IDLE, target=AgentState.SCROLLING
            )
        ]
        sc = Statechart(states=states, transitions=transitions, initial=AgentState.IDLE)

        result = sc.fire(
            trigger="unknown", current_state=AgentState.IDLE, agent=None, context=None
        )
        assert result is None

    def test_fire_returns_none_when_no_transition_matches_state(self):
        """fire() should return None when no transition matches current state."""
        from prism.statechart.statechart import Statechart

        states = {AgentState.IDLE, AgentState.SCROLLING}
        transitions = [
            Transition(
                trigger="start", source=AgentState.IDLE, target=AgentState.SCROLLING
            )
        ]
        sc = Statechart(states=states, transitions=transitions, initial=AgentState.IDLE)

        result = sc.fire(
            trigger="start",
            current_state=AgentState.SCROLLING,
            agent=None,
            context=None,
        )
        assert result is None

    def test_fire_evaluates_guard_and_fires_when_true(self):
        """fire() should fire transition when guard returns True."""
        from prism.statechart.statechart import Statechart

        def allow_guard(agent, context):
            return True

        states = {AgentState.IDLE, AgentState.SCROLLING}
        transitions = [
            Transition(
                trigger="start",
                source=AgentState.IDLE,
                target=AgentState.SCROLLING,
                guard=allow_guard,
            )
        ]
        sc = Statechart(states=states, transitions=transitions, initial=AgentState.IDLE)

        result = sc.fire(
            trigger="start", current_state=AgentState.IDLE, agent=None, context=None
        )
        assert result == AgentState.SCROLLING

    def test_fire_skips_transition_when_guard_returns_false(self):
        """fire() should skip transition when guard returns False."""
        from prism.statechart.statechart import Statechart

        def deny_guard(agent, context):
            return False

        states = {AgentState.IDLE, AgentState.SCROLLING}
        transitions = [
            Transition(
                trigger="start",
                source=AgentState.IDLE,
                target=AgentState.SCROLLING,
                guard=deny_guard,
            )
        ]
        sc = Statechart(states=states, transitions=transitions, initial=AgentState.IDLE)

        result = sc.fire(
            trigger="start", current_state=AgentState.IDLE, agent=None, context=None
        )
        assert result is None

    def test_fire_evaluates_guards_in_definition_order(self):
        """fire() should evaluate guards in definition order."""
        from prism.statechart.statechart import Statechart

        call_order = []

        def first_guard(agent, context):
            call_order.append("first")
            return False

        def second_guard(agent, context):
            call_order.append("second")
            return True

        states = {AgentState.IDLE, AgentState.SCROLLING, AgentState.EVALUATING}
        transitions = [
            Transition(
                trigger="start",
                source=AgentState.IDLE,
                target=AgentState.SCROLLING,
                guard=first_guard,
            ),
            Transition(
                trigger="start",
                source=AgentState.IDLE,
                target=AgentState.EVALUATING,
                guard=second_guard,
            ),
        ]
        sc = Statechart(states=states, transitions=transitions, initial=AgentState.IDLE)

        sc.fire(
            trigger="start", current_state=AgentState.IDLE, agent=None, context=None
        )
        assert call_order == ["first", "second"]

    def test_fire_first_matching_guard_wins(self):
        """fire() should use first transition whose guard returns True."""
        from prism.statechart.statechart import Statechart

        def first_true_guard(agent, context):
            return True

        def second_true_guard(agent, context):
            return True

        states = {AgentState.IDLE, AgentState.SCROLLING, AgentState.EVALUATING}
        transitions = [
            Transition(
                trigger="start",
                source=AgentState.IDLE,
                target=AgentState.SCROLLING,
                guard=first_true_guard,
            ),
            Transition(
                trigger="start",
                source=AgentState.IDLE,
                target=AgentState.EVALUATING,
                guard=second_true_guard,
            ),
        ]
        sc = Statechart(states=states, transitions=transitions, initial=AgentState.IDLE)

        result = sc.fire(
            trigger="start", current_state=AgentState.IDLE, agent=None, context=None
        )
        assert result == AgentState.SCROLLING  # First matching transition wins

    def test_fire_passes_agent_and_context_to_guard(self):
        """fire() should pass agent and context to guard function."""
        from prism.statechart.statechart import Statechart

        received_args = {}

        def capture_guard(agent, context):
            received_args["agent"] = agent
            received_args["context"] = context
            return True

        states = {AgentState.IDLE, AgentState.SCROLLING}
        transitions = [
            Transition(
                trigger="start",
                source=AgentState.IDLE,
                target=AgentState.SCROLLING,
                guard=capture_guard,
            )
        ]
        sc = Statechart(states=states, transitions=transitions, initial=AgentState.IDLE)

        test_agent = {"name": "test_agent"}
        test_context = {"post_id": "123"}

        sc.fire(
            trigger="start",
            current_state=AgentState.IDLE,
            agent=test_agent,
            context=test_context,
        )

        assert received_args["agent"] == test_agent
        assert received_args["context"] == test_context


class TestStatechartGuardFailSafe:
    """Tests for guard exception handling (T011)."""

    def test_guard_exception_treated_as_false(self):
        """Guard that raises exception should be treated as False."""
        from prism.statechart.statechart import Statechart

        def failing_guard(agent, context):
            raise RuntimeError("Guard error")

        def passing_guard(agent, context):
            return True

        states = {AgentState.IDLE, AgentState.SCROLLING, AgentState.EVALUATING}
        transitions = [
            Transition(
                trigger="start",
                source=AgentState.IDLE,
                target=AgentState.SCROLLING,
                guard=failing_guard,
            ),
            Transition(
                trigger="start",
                source=AgentState.IDLE,
                target=AgentState.EVALUATING,
                guard=passing_guard,
            ),
        ]
        sc = Statechart(states=states, transitions=transitions, initial=AgentState.IDLE)

        # Should not raise, should continue to next transition
        result = sc.fire(
            trigger="start", current_state=AgentState.IDLE, agent=None, context=None
        )
        assert result == AgentState.EVALUATING

    def test_guard_non_boolean_coerced_to_bool_truthy(self):
        """Guard returning truthy non-boolean should be coerced to True."""
        from prism.statechart.statechart import Statechart

        def truthy_guard(agent, context):
            return "truthy string"  # Non-boolean but truthy

        states = {AgentState.IDLE, AgentState.SCROLLING}
        transitions = [
            Transition(
                trigger="start",
                source=AgentState.IDLE,
                target=AgentState.SCROLLING,
                guard=truthy_guard,
            )
        ]
        sc = Statechart(states=states, transitions=transitions, initial=AgentState.IDLE)

        result = sc.fire(
            trigger="start", current_state=AgentState.IDLE, agent=None, context=None
        )
        assert result == AgentState.SCROLLING

    def test_guard_non_boolean_coerced_to_bool_falsy(self):
        """Guard returning falsy non-boolean should be coerced to False."""
        from prism.statechart.statechart import Statechart

        def falsy_guard(agent, context):
            return 0  # Non-boolean but falsy

        def passing_guard(agent, context):
            return True

        states = {AgentState.IDLE, AgentState.SCROLLING, AgentState.EVALUATING}
        transitions = [
            Transition(
                trigger="start",
                source=AgentState.IDLE,
                target=AgentState.SCROLLING,
                guard=falsy_guard,
            ),
            Transition(
                trigger="start",
                source=AgentState.IDLE,
                target=AgentState.EVALUATING,
                guard=passing_guard,
            ),
        ]
        sc = Statechart(states=states, transitions=transitions, initial=AgentState.IDLE)

        result = sc.fire(
            trigger="start", current_state=AgentState.IDLE, agent=None, context=None
        )
        assert result == AgentState.EVALUATING

    def test_guard_exception_continues_to_next_candidate(self):
        """After guard exception, should continue to next candidate transition."""
        from prism.statechart.statechart import Statechart

        call_log = []

        def first_failing_guard(agent, context):
            call_log.append("first")
            raise ValueError("Boom!")

        def second_passing_guard(agent, context):
            call_log.append("second")
            return True

        states = {AgentState.IDLE, AgentState.SCROLLING, AgentState.EVALUATING}
        transitions = [
            Transition(
                trigger="start",
                source=AgentState.IDLE,
                target=AgentState.SCROLLING,
                guard=first_failing_guard,
            ),
            Transition(
                trigger="start",
                source=AgentState.IDLE,
                target=AgentState.EVALUATING,
                guard=second_passing_guard,
            ),
        ]
        sc = Statechart(states=states, transitions=transitions, initial=AgentState.IDLE)

        result = sc.fire(
            trigger="start", current_state=AgentState.IDLE, agent=None, context=None
        )

        # Both guards should have been called
        assert call_log == ["first", "second"]
        # Second transition should have fired
        assert result == AgentState.EVALUATING

    def test_all_guards_fail_returns_none(self):
        """When all guards fail (exception or False), should return None."""
        from prism.statechart.statechart import Statechart

        def failing_guard(agent, context):
            raise RuntimeError("Guard error")

        def false_guard(agent, context):
            return False

        states = {AgentState.IDLE, AgentState.SCROLLING, AgentState.EVALUATING}
        transitions = [
            Transition(
                trigger="start",
                source=AgentState.IDLE,
                target=AgentState.SCROLLING,
                guard=failing_guard,
            ),
            Transition(
                trigger="start",
                source=AgentState.IDLE,
                target=AgentState.EVALUATING,
                guard=false_guard,
            ),
        ]
        sc = Statechart(states=states, transitions=transitions, initial=AgentState.IDLE)

        result = sc.fire(
            trigger="start", current_state=AgentState.IDLE, agent=None, context=None
        )
        assert result is None


class TestStatechartValidTriggers:
    """Tests for Statechart.valid_triggers() (T013)."""

    def test_valid_triggers_returns_triggers_from_state(self):
        """valid_triggers() should return triggers available from given state."""
        from prism.statechart.statechart import Statechart

        states = {AgentState.IDLE, AgentState.SCROLLING, AgentState.EVALUATING}
        transitions = [
            Transition(
                trigger="start", source=AgentState.IDLE, target=AgentState.SCROLLING
            ),
            Transition(
                trigger="evaluate",
                source=AgentState.SCROLLING,
                target=AgentState.EVALUATING,
            ),
            Transition(
                trigger="scroll_more",
                source=AgentState.SCROLLING,
                target=AgentState.SCROLLING,
            ),
        ]
        sc = Statechart(states=states, transitions=transitions, initial=AgentState.IDLE)

        # From IDLE, only "start" is available
        triggers = sc.valid_triggers(AgentState.IDLE)
        assert triggers == ["start"]

        # From SCROLLING, "evaluate" and "scroll_more" are available
        triggers = sc.valid_triggers(AgentState.SCROLLING)
        assert set(triggers) == {"evaluate", "scroll_more"}

    def test_valid_triggers_returns_empty_for_state_with_no_transitions(self):
        """valid_triggers() returns empty list for state with no outgoing."""
        from prism.statechart.statechart import Statechart

        states = {AgentState.IDLE, AgentState.SCROLLING, AgentState.RESTING}
        transitions = [
            Transition(
                trigger="start", source=AgentState.IDLE, target=AgentState.SCROLLING
            ),
            Transition(
                trigger="rest", source=AgentState.SCROLLING, target=AgentState.RESTING
            ),
        ]
        sc = Statechart(states=states, transitions=transitions, initial=AgentState.IDLE)

        # RESTING has no outgoing transitions
        triggers = sc.valid_triggers(AgentState.RESTING)
        assert triggers == []

    def test_valid_triggers_deduplicates_triggers(self):
        """valid_triggers() returns unique triggers even with multiple transitions."""
        from prism.statechart.statechart import Statechart

        states = {AgentState.IDLE, AgentState.SCROLLING, AgentState.EVALUATING}
        transitions = [
            Transition(
                trigger="start",
                source=AgentState.IDLE,
                target=AgentState.SCROLLING,
                guard=lambda a, c: True,
            ),
            Transition(
                trigger="start",
                source=AgentState.IDLE,
                target=AgentState.EVALUATING,
                guard=lambda a, c: False,
            ),
        ]
        sc = Statechart(states=states, transitions=transitions, initial=AgentState.IDLE)

        # Should return "start" only once even though there are 2 transitions
        triggers = sc.valid_triggers(AgentState.IDLE)
        assert triggers == ["start"]


class TestStatechartActionExecution:
    """Tests for action execution in fire()."""

    def test_fire_executes_action_when_transition_matches(self):
        """fire() should execute action when transition fires."""
        from prism.statechart.statechart import Statechart

        action_called = []

        def capture_action(agent, context):
            action_called.append((agent, context))

        states = {AgentState.IDLE, AgentState.SCROLLING}
        transitions = [
            Transition(
                trigger="start",
                source=AgentState.IDLE,
                target=AgentState.SCROLLING,
                action=capture_action,
            )
        ]
        sc = Statechart(states=states, transitions=transitions, initial=AgentState.IDLE)

        test_agent = {"name": "test"}
        test_context = {"post_id": "123"}

        sc.fire(
            trigger="start",
            current_state=AgentState.IDLE,
            agent=test_agent,
            context=test_context,
        )

        assert len(action_called) == 1
        assert action_called[0] == (test_agent, test_context)

    def test_fire_action_exception_does_not_prevent_transition(self):
        """Action exception should not prevent transition (fail-safe)."""
        from prism.statechart.statechart import Statechart

        def failing_action(agent, context):
            raise RuntimeError("Action failed")

        states = {AgentState.IDLE, AgentState.SCROLLING}
        transitions = [
            Transition(
                trigger="start",
                source=AgentState.IDLE,
                target=AgentState.SCROLLING,
                action=failing_action,
            )
        ]
        sc = Statechart(states=states, transitions=transitions, initial=AgentState.IDLE)

        result = sc.fire(
            trigger="start", current_state=AgentState.IDLE, agent=None, context=None
        )

        # Transition should still succeed despite action failure
        assert result == AgentState.SCROLLING

    def test_fire_does_not_call_action_when_no_transition_matches(self):
        """fire() should not call action when no transition matches."""
        from prism.statechart.statechart import Statechart

        action_called = []

        def capture_action(agent, context):
            action_called.append(True)

        states = {AgentState.IDLE, AgentState.SCROLLING}
        transitions = [
            Transition(
                trigger="start",
                source=AgentState.IDLE,
                target=AgentState.SCROLLING,
                action=capture_action,
            )
        ]
        sc = Statechart(states=states, transitions=transitions, initial=AgentState.IDLE)

        # Wrong trigger - should not match
        sc.fire(
            trigger="unknown", current_state=AgentState.IDLE, agent=None, context=None
        )

        assert len(action_called) == 0


class TestStatechartValidTargets:
    """Tests for Statechart.valid_targets() (T014)."""

    def test_valid_targets_returns_targets_for_trigger_from_state(self):
        """valid_targets() should return target states for trigger from given state."""
        from prism.statechart.statechart import Statechart

        states = {AgentState.IDLE, AgentState.SCROLLING, AgentState.EVALUATING}
        transitions = [
            Transition(
                trigger="decide",
                source=AgentState.EVALUATING,
                target=AgentState.SCROLLING,
                guard=lambda a, c: True,
            ),
            Transition(
                trigger="decide",
                source=AgentState.EVALUATING,
                target=AgentState.IDLE,
                guard=lambda a, c: False,
            ),
        ]
        sc = Statechart(states=states, transitions=transitions, initial=AgentState.IDLE)

        # From EVALUATING with "decide" trigger, can go to SCROLLING or IDLE
        targets = sc.valid_targets(AgentState.EVALUATING, "decide")
        assert set(targets) == {AgentState.SCROLLING, AgentState.IDLE}

    def test_valid_targets_returns_empty_when_no_matching_transitions(self):
        """valid_targets() should return empty list when no matching transitions."""
        from prism.statechart.statechart import Statechart

        states = {AgentState.IDLE, AgentState.SCROLLING}
        transitions = [
            Transition(
                trigger="start", source=AgentState.IDLE, target=AgentState.SCROLLING
            )
        ]
        sc = Statechart(states=states, transitions=transitions, initial=AgentState.IDLE)

        # No transitions from SCROLLING with "start" trigger
        targets = sc.valid_targets(AgentState.SCROLLING, "start")
        assert targets == []

        # No transitions from IDLE with "unknown" trigger
        targets = sc.valid_targets(AgentState.IDLE, "unknown")
        assert targets == []

    def test_valid_targets_includes_all_targets_for_trigger(self):
        """valid_targets() should include all possible targets for a trigger."""
        from prism.statechart.statechart import Statechart

        states = {
            AgentState.EVALUATING,
            AgentState.ENGAGING_LIKE,
            AgentState.ENGAGING_REPLY,
            AgentState.ENGAGING_RESHARE,
        }
        transitions = [
            Transition(
                trigger="engage",
                source=AgentState.EVALUATING,
                target=AgentState.ENGAGING_LIKE,
            ),
            Transition(
                trigger="engage",
                source=AgentState.EVALUATING,
                target=AgentState.ENGAGING_REPLY,
            ),
            Transition(
                trigger="engage",
                source=AgentState.EVALUATING,
                target=AgentState.ENGAGING_RESHARE,
            ),
        ]
        sc = Statechart(
            states=states, transitions=transitions, initial=AgentState.EVALUATING
        )

        targets = sc.valid_targets(AgentState.EVALUATING, "engage")
        assert set(targets) == {
            AgentState.ENGAGING_LIKE,
            AgentState.ENGAGING_REPLY,
            AgentState.ENGAGING_RESHARE,
        }
