"""Tests for simulation round controller.

This module tests the RoundController class that orchestrates
simulation rounds, agent processing, and checkpointing.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from prism.simulation.checkpointer import Checkpointer
from prism.simulation.config import SimulationConfig
from prism.simulation.controller import RoundController
from prism.simulation.results import DecisionResult, RoundResult, SimulationResult
from prism.simulation.state import SimulationState
from prism.simulation.statechart_factory import create_social_media_statechart
from prism.statechart.states import AgentState


def create_mock_agent(
    agent_id: str = "agent_1",
    state: AgentState = AgentState.IDLE,
) -> MagicMock:
    """Create a mock agent for testing."""
    agent = MagicMock()
    agent.agent_id = agent_id
    agent.name = f"Agent {agent_id}"
    agent.state = state
    agent.ticks_in_state = 0
    agent.interests = ["tech"]
    agent.personality = "curious"
    agent.engagement_threshold = 0.5
    return agent


def create_mock_round_executor() -> MagicMock:
    """Create a mock AgentRoundExecutor."""
    executor = MagicMock()
    executor.execute = AsyncMock(
        return_value=DecisionResult(
            agent_id="agent_1",
            trigger="start_browsing",
            from_state=AgentState.IDLE,
            to_state=AgentState.SCROLLING,
        )
    )
    return executor


class TestRoundControllerRunSimulation:
    """Tests for RoundController.run_simulation method."""

    @pytest.mark.asyncio
    async def test_run_simulation_iterates_rounds(self, tmp_path: Path) -> None:
        """T117: run_simulation iterates for max_rounds."""
        # Arrange
        config = SimulationConfig(max_rounds=3, checkpoint_dir=None)
        agent = create_mock_agent()
        statechart = create_social_media_statechart()
        state = SimulationState(posts=[], agents=[agent], statechart=statechart)

        round_executor = create_mock_round_executor()
        controller = RoundController(round_executor=round_executor)

        # Act
        result = await controller.run_simulation(config=config, state=state)

        # Assert
        assert result.total_rounds == 3
        # Each round, each agent gets executed once
        assert round_executor.execute.await_count == 3  # 1 agent × 3 rounds

    @pytest.mark.asyncio
    async def test_controller_processes_all_agents_each_round(
        self, tmp_path: Path
    ) -> None:
        """T119: controller processes all agents each round."""
        # Arrange
        config = SimulationConfig(max_rounds=2, checkpoint_dir=None)
        agents = [create_mock_agent(f"agent_{i}") for i in range(5)]
        statechart = create_social_media_statechart()
        state = SimulationState(posts=[], agents=agents, statechart=statechart)

        round_executor = create_mock_round_executor()
        controller = RoundController(round_executor=round_executor)

        # Act
        await controller.run_simulation(config=config, state=state)

        # Assert - 5 agents × 2 rounds = 10 executions
        assert round_executor.execute.await_count == 10

    @pytest.mark.asyncio
    async def test_controller_saves_checkpoints_at_frequency(
        self, tmp_path: Path
    ) -> None:
        """T121: controller saves checkpoints at configured frequency."""
        # Arrange
        checkpoint_dir = tmp_path / "checkpoints"
        config = SimulationConfig(
            max_rounds=6,
            checkpoint_frequency=2,  # Every 2 rounds
            checkpoint_dir=checkpoint_dir,
        )
        agent = create_mock_agent()
        statechart = create_social_media_statechart()
        state = SimulationState(posts=[], agents=[agent], statechart=statechart)

        round_executor = create_mock_round_executor()
        controller = RoundController(round_executor=round_executor)

        # Act
        await controller.run_simulation(config=config, state=state)

        # Assert - should save at rounds 2, 4, 6 (every 2 rounds)
        # Checkpoints are saved AFTER advancing round, so we save at 2, 4, 6
        checkpoints = list(checkpoint_dir.glob("checkpoint_round_*.json"))
        assert len(checkpoints) == 3

    @pytest.mark.asyncio
    async def test_controller_skips_checkpoints_when_dir_is_none(self) -> None:
        """T123: controller skips checkpoints when checkpoint_dir is None."""
        # Arrange
        config = SimulationConfig(max_rounds=3, checkpoint_dir=None)
        agent = create_mock_agent()
        statechart = create_social_media_statechart()
        state = SimulationState(posts=[], agents=[agent], statechart=statechart)

        round_executor = create_mock_round_executor()
        controller = RoundController(round_executor=round_executor)

        # Act - should not raise even without checkpoint dir
        result = await controller.run_simulation(config=config, state=state)

        # Assert
        assert result.total_rounds == 3

    @pytest.mark.asyncio
    async def test_controller_advances_round_number(self) -> None:
        """T125: controller advances round_number each round."""
        # Arrange
        config = SimulationConfig(max_rounds=3, checkpoint_dir=None)
        agent = create_mock_agent()
        statechart = create_social_media_statechart()
        state = SimulationState(posts=[], agents=[agent], statechart=statechart)

        round_executor = create_mock_round_executor()
        controller = RoundController(round_executor=round_executor)

        # Track round numbers during execution
        round_numbers = []

        async def track_round(agent, state):
            round_numbers.append(state.round_number)
            return DecisionResult(
                agent_id=agent.agent_id,
                trigger="start_browsing",
                from_state=AgentState.IDLE,
                to_state=AgentState.SCROLLING,
            )

        round_executor.execute = AsyncMock(side_effect=track_round)

        # Act
        await controller.run_simulation(config=config, state=state)

        # Assert - round numbers should be 0, 1, 2 during execution
        # (advance_round is called AFTER each round completes)
        assert round_numbers == [0, 1, 2]

    @pytest.mark.asyncio
    async def test_controller_returns_simulation_result(self) -> None:
        """T127: controller returns SimulationResult with metrics."""
        # Arrange
        config = SimulationConfig(max_rounds=2, checkpoint_dir=None)
        agent = create_mock_agent()
        statechart = create_social_media_statechart()
        state = SimulationState(posts=[], agents=[agent], statechart=statechart)
        state.metrics.total_likes = 10

        round_executor = create_mock_round_executor()
        controller = RoundController(round_executor=round_executor)

        # Act
        result = await controller.run_simulation(config=config, state=state)

        # Assert
        assert isinstance(result, SimulationResult)
        assert result.total_rounds == 2
        assert result.final_metrics.total_likes == 10


class TestRoundControllerRunRound:
    """Tests for RoundController.run_round method."""

    @pytest.mark.asyncio
    async def test_run_round_executes_single_round(self) -> None:
        """T129: run_round executes a single round."""
        # Arrange
        agent = create_mock_agent()
        statechart = create_social_media_statechart()
        state = SimulationState(posts=[], agents=[agent], statechart=statechart)

        round_executor = create_mock_round_executor()
        controller = RoundController(round_executor=round_executor)

        # Act
        round_result = await controller.run_round(state=state)

        # Assert
        assert isinstance(round_result, RoundResult)
        assert round_result.round_number == 0
        assert len(round_result.decisions) == 1

    @pytest.mark.asyncio
    async def test_run_round_processes_all_agents(self) -> None:
        """run_round processes all agents in the state."""
        # Arrange
        agents = [create_mock_agent(f"agent_{i}") for i in range(3)]
        statechart = create_social_media_statechart()
        state = SimulationState(posts=[], agents=agents, statechart=statechart)

        round_executor = create_mock_round_executor()
        controller = RoundController(round_executor=round_executor)

        # Act
        round_result = await controller.run_round(state=state)

        # Assert
        assert len(round_result.decisions) == 3
        assert round_executor.execute.await_count == 3


class TestRoundControllerResumeFromCheckpoint:
    """Tests for RoundController.resume_from_checkpoint method."""

    @pytest.mark.asyncio
    async def test_resume_from_checkpoint_loads_and_continues(
        self, tmp_path: Path
    ) -> None:
        """T131: resume_from_checkpoint loads state and continues simulation."""
        # Arrange - first, create a checkpoint
        checkpoint_dir = tmp_path / "checkpoints"
        checkpointer = Checkpointer(checkpoint_dir)
        agent = create_mock_agent()
        statechart = create_social_media_statechart()

        initial_state = SimulationState(
            posts=[],
            agents=[agent],
            statechart=statechart,
            round_number=5,
        )
        initial_state.metrics.total_likes = 100
        checkpoint_path = checkpointer.save(initial_state)

        # Config to run 3 more rounds (total 8)
        config = SimulationConfig(
            max_rounds=8,
            checkpoint_dir=checkpoint_dir,
            checkpoint_frequency=100,  # Don't checkpoint during test
        )

        round_executor = create_mock_round_executor()
        controller = RoundController(round_executor=round_executor)

        # Act - resume from checkpoint at round 5, run until round 8
        result = await controller.resume_from_checkpoint(
            checkpoint_path=checkpoint_path,
            config=config,
            statechart=statechart,
        )

        # Assert - should have run rounds 5, 6, 7 (3 rounds)
        # Note: resumed state starts at round 5, runs until max_rounds=8
        assert result.total_rounds == 8
        # Executor called for rounds 5, 6, 7 (3 rounds × 1 agent)
        assert round_executor.execute.await_count == 3

    @pytest.mark.asyncio
    async def test_resume_preserves_metrics(self, tmp_path: Path) -> None:
        """Resume preserves metrics from checkpoint."""
        # Arrange
        checkpoint_dir = tmp_path / "checkpoints"
        checkpointer = Checkpointer(checkpoint_dir)
        agent = create_mock_agent()
        statechart = create_social_media_statechart()

        initial_state = SimulationState(
            posts=[],
            agents=[agent],
            statechart=statechart,
            round_number=3,
        )
        initial_state.metrics.total_likes = 50
        initial_state.metrics.total_reshares = 25
        checkpoint_path = checkpointer.save(initial_state)

        config = SimulationConfig(
            max_rounds=5,
            checkpoint_dir=None,  # No further checkpoints
        )

        round_executor = create_mock_round_executor()
        controller = RoundController(round_executor=round_executor)

        # Act
        result = await controller.resume_from_checkpoint(
            checkpoint_path=checkpoint_path,
            config=config,
            statechart=statechart,
        )

        # Assert - metrics should be preserved
        assert result.final_metrics.total_likes == 50
        assert result.final_metrics.total_reshares == 25
