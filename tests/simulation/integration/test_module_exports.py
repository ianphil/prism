"""Tests for simulation module exports.

Verifies that the public API is properly exported from __init__.py files.
"""


class TestSimulationModuleExports:
    """T137: Verify prism/simulation/__init__.py exports."""

    def test_can_import_simulation_config(self) -> None:
        """SimulationConfig should be importable from prism.simulation."""
        from prism.simulation import SimulationConfig

        assert SimulationConfig is not None

    def test_can_import_load_config(self) -> None:
        """load_config should be importable from prism.simulation."""
        from prism.simulation import load_config

        assert load_config is not None

    def test_can_import_simulation_state(self) -> None:
        """SimulationState should be importable from prism.simulation."""
        from prism.simulation import SimulationState

        assert SimulationState is not None

    def test_can_import_engagement_metrics(self) -> None:
        """EngagementMetrics should be importable from prism.simulation."""
        from prism.simulation import EngagementMetrics

        assert EngagementMetrics is not None

    def test_can_import_round_controller(self) -> None:
        """RoundController should be importable from prism.simulation."""
        from prism.simulation import RoundController

        assert RoundController is not None

    def test_can_import_checkpointer(self) -> None:
        """Checkpointer should be importable from prism.simulation."""
        from prism.simulation import Checkpointer

        assert Checkpointer is not None

    def test_can_import_result_types(self) -> None:
        """Result types should be importable from prism.simulation."""
        from prism.simulation import (
            ActionResult,
            DecisionResult,
            RoundResult,
            SimulationResult,
        )

        assert ActionResult is not None
        assert DecisionResult is not None
        assert RoundResult is not None
        assert SimulationResult is not None

    def test_can_import_statechart_factory(self) -> None:
        """create_social_media_statechart should be importable from prism.simulation."""
        from prism.simulation import create_social_media_statechart

        assert create_social_media_statechart is not None

    def test_can_import_determine_trigger(self) -> None:
        """determine_trigger should be importable from prism.simulation."""
        from prism.simulation import determine_trigger

        assert determine_trigger is not None


class TestExecutorsModuleExports:
    """T139: Verify prism/simulation/executors/__init__.py exports."""

    def test_can_import_feed_retrieval_executor(self) -> None:
        """FeedRetrievalExecutor should be importable from executors."""
        from prism.simulation.executors import FeedRetrievalExecutor

        assert FeedRetrievalExecutor is not None

    def test_can_import_agent_decision_executor(self) -> None:
        """AgentDecisionExecutor should be importable from executors."""
        from prism.simulation.executors import AgentDecisionExecutor

        assert AgentDecisionExecutor is not None

    def test_can_import_state_update_executor(self) -> None:
        """StateUpdateExecutor should be importable from executors."""
        from prism.simulation.executors import StateUpdateExecutor

        assert StateUpdateExecutor is not None

    def test_can_import_logging_executor(self) -> None:
        """LoggingExecutor should be importable from executors."""
        from prism.simulation.executors import LoggingExecutor

        assert LoggingExecutor is not None

    def test_can_import_agent_round_executor(self) -> None:
        """AgentRoundExecutor should be importable from executors."""
        from prism.simulation.executors import AgentRoundExecutor

        assert AgentRoundExecutor is not None

    def test_all_list_is_complete(self) -> None:
        """__all__ should list all expected exports."""
        from prism.simulation import executors

        expected = [
            "FeedRetrievalExecutor",
            "AgentDecisionExecutor",
            "StateUpdateExecutor",
            "LoggingExecutor",
            "AgentRoundExecutor",
        ]
        for name in expected:
            assert name in executors.__all__, f"Expected {name} in __all__"
