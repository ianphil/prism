"""Tests for simulation result types (T021-T028)."""


class TestActionResult:
    """T021: Test ActionResult dataclass."""

    def test_action_result_has_action_field(self):
        """ActionResult should have an action field."""
        from prism.simulation.results import ActionResult

        result = ActionResult(action="like", target_post_id="post_001")
        assert result.action == "like"

    def test_action_result_has_target_post_id_field(self):
        """ActionResult should have target_post_id field."""
        from prism.simulation.results import ActionResult

        result = ActionResult(action="reply", target_post_id="post_002")
        assert result.target_post_id == "post_002"

    def test_action_result_target_post_id_optional(self):
        """ActionResult target_post_id should be optional (None for compose)."""
        from prism.simulation.results import ActionResult

        result = ActionResult(action="compose", target_post_id=None)
        assert result.target_post_id is None

    def test_action_result_has_content_field(self):
        """ActionResult should have optional content field."""
        from prism.simulation.results import ActionResult

        result = ActionResult(
            action="reply", target_post_id="post_001", content="Great post!"
        )
        assert result.content == "Great post!"

    def test_action_result_content_defaults_to_none(self):
        """ActionResult content should default to None."""
        from prism.simulation.results import ActionResult

        result = ActionResult(action="like", target_post_id="post_001")
        assert result.content is None

    def test_action_result_is_dataclass(self):
        """ActionResult should be a dataclass."""
        from dataclasses import is_dataclass

        from prism.simulation.results import ActionResult

        assert is_dataclass(ActionResult)


class TestDecisionResult:
    """T023: Test DecisionResult dataclass."""

    def test_decision_result_has_agent_id(self):
        """DecisionResult should have agent_id field."""
        from prism.simulation.results import DecisionResult
        from prism.statechart.states import AgentState

        result = DecisionResult(
            agent_id="agent_001",
            trigger="start_browsing",
            from_state=AgentState.IDLE,
            to_state=AgentState.SCROLLING,
        )
        assert result.agent_id == "agent_001"

    def test_decision_result_has_trigger(self):
        """DecisionResult should have trigger field."""
        from prism.simulation.results import DecisionResult
        from prism.statechart.states import AgentState

        result = DecisionResult(
            agent_id="agent_001",
            trigger="sees_post",
            from_state=AgentState.SCROLLING,
            to_state=AgentState.EVALUATING,
        )
        assert result.trigger == "sees_post"

    def test_decision_result_has_from_state(self):
        """DecisionResult should have from_state field."""
        from prism.simulation.results import DecisionResult
        from prism.statechart.states import AgentState

        result = DecisionResult(
            agent_id="agent_001",
            trigger="decides",
            from_state=AgentState.EVALUATING,
            to_state=AgentState.COMPOSING,
        )
        assert result.from_state == AgentState.EVALUATING

    def test_decision_result_has_to_state(self):
        """DecisionResult should have to_state field."""
        from prism.simulation.results import DecisionResult
        from prism.statechart.states import AgentState

        result = DecisionResult(
            agent_id="agent_001",
            trigger="decides",
            from_state=AgentState.EVALUATING,
            to_state=AgentState.ENGAGING_LIKE,
        )
        assert result.to_state == AgentState.ENGAGING_LIKE

    def test_decision_result_has_action_optional(self):
        """DecisionResult should have optional action field."""
        from prism.simulation.results import ActionResult, DecisionResult
        from prism.statechart.states import AgentState

        action = ActionResult(action="like", target_post_id="post_001")
        result = DecisionResult(
            agent_id="agent_001",
            trigger="decides",
            from_state=AgentState.EVALUATING,
            to_state=AgentState.ENGAGING_LIKE,
            action=action,
        )
        assert result.action == action

    def test_decision_result_action_defaults_to_none(self):
        """DecisionResult action should default to None."""
        from prism.simulation.results import DecisionResult
        from prism.statechart.states import AgentState

        result = DecisionResult(
            agent_id="agent_001",
            trigger="start_browsing",
            from_state=AgentState.IDLE,
            to_state=AgentState.SCROLLING,
        )
        assert result.action is None

    def test_decision_result_is_dataclass(self):
        """DecisionResult should be a dataclass."""
        from dataclasses import is_dataclass

        from prism.simulation.results import DecisionResult

        assert is_dataclass(DecisionResult)


class TestRoundResult:
    """T025: Test RoundResult dataclass."""

    def test_round_result_has_round_number(self):
        """RoundResult should have round_number field."""
        from prism.simulation.results import RoundResult

        result = RoundResult(round_number=5, decisions=[])
        assert result.round_number == 5

    def test_round_result_has_decisions_list(self):
        """RoundResult should have decisions field (list)."""
        from prism.simulation.results import DecisionResult, RoundResult
        from prism.statechart.states import AgentState

        decision = DecisionResult(
            agent_id="agent_001",
            trigger="start_browsing",
            from_state=AgentState.IDLE,
            to_state=AgentState.SCROLLING,
        )
        result = RoundResult(round_number=1, decisions=[decision])
        assert len(result.decisions) == 1
        assert result.decisions[0] == decision

    def test_round_result_is_dataclass(self):
        """RoundResult should be a dataclass."""
        from dataclasses import is_dataclass

        from prism.simulation.results import RoundResult

        assert is_dataclass(RoundResult)


class TestSimulationResult:
    """T027: Test SimulationResult dataclass."""

    def test_simulation_result_has_total_rounds(self):
        """SimulationResult should have total_rounds field."""
        from prism.simulation.results import SimulationResult
        from prism.simulation.state import EngagementMetrics

        metrics = EngagementMetrics()
        result = SimulationResult(total_rounds=10, final_metrics=metrics, rounds=[])
        assert result.total_rounds == 10

    def test_simulation_result_has_final_metrics(self):
        """SimulationResult should have final_metrics field."""
        from prism.simulation.results import SimulationResult
        from prism.simulation.state import EngagementMetrics

        metrics = EngagementMetrics(total_likes=50, total_reshares=20)
        result = SimulationResult(total_rounds=10, final_metrics=metrics, rounds=[])
        assert result.final_metrics.total_likes == 50
        assert result.final_metrics.total_reshares == 20

    def test_simulation_result_has_rounds_list(self):
        """SimulationResult should have rounds field (list of RoundResult)."""
        from prism.simulation.results import RoundResult, SimulationResult
        from prism.simulation.state import EngagementMetrics

        metrics = EngagementMetrics()
        round1 = RoundResult(round_number=0, decisions=[])
        round2 = RoundResult(round_number=1, decisions=[])
        result = SimulationResult(
            total_rounds=2, final_metrics=metrics, rounds=[round1, round2]
        )
        assert len(result.rounds) == 2
        assert result.rounds[0].round_number == 0
        assert result.rounds[1].round_number == 1

    def test_simulation_result_is_dataclass(self):
        """SimulationResult should be a dataclass."""
        from dataclasses import is_dataclass

        from prism.simulation.results import SimulationResult

        assert is_dataclass(SimulationResult)
