"""Tests for LoggingExecutor."""

import json
import logging
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from prism.simulation.executors.logging import LoggingExecutor
from prism.simulation.results import ActionResult, DecisionResult
from prism.simulation.state import SimulationState
from prism.simulation.statechart_factory import create_social_media_statechart
from prism.statechart.states import AgentState


def create_mock_agent() -> MagicMock:
    """Create a mock agent."""
    agent = MagicMock()
    agent.agent_id = "test_agent"
    agent.state = AgentState.SCROLLING
    return agent


def create_test_state() -> SimulationState:
    """Create a test SimulationState."""
    return SimulationState(
        posts=[],
        agents=[create_mock_agent()],
        statechart=create_social_media_statechart(),
        round_number=5,
    )


class TestLoggingExecutor:
    """Tests for LoggingExecutor."""

    @pytest.mark.asyncio
    async def test_execute_logs_json_entry(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """T091: executor should log JSON entry."""
        # Arrange
        agent = create_mock_agent()
        state = create_test_state()

        decision = DecisionResult(
            agent_id="test_agent",
            trigger="sees_post",
            from_state=AgentState.SCROLLING,
            to_state=AgentState.EVALUATING,
            action=ActionResult(action="scroll", target_post_id=None),
        )

        executor = LoggingExecutor()

        # Act
        with caplog.at_level(logging.INFO, logger="prism.simulation.decisions"):
            await executor.execute(agent=agent, state=state, decision=decision)

        # Assert - log entry is valid JSON
        assert len(caplog.records) >= 1
        log_text = caplog.records[-1].message
        entry = json.loads(log_text)
        assert isinstance(entry, dict)

    @pytest.mark.asyncio
    async def test_log_entry_contains_required_fields(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """T093: log entry should contain required fields."""
        # Arrange
        agent = create_mock_agent()
        state = create_test_state()

        decision = DecisionResult(
            agent_id="test_agent",
            trigger="sees_post",
            from_state=AgentState.SCROLLING,
            to_state=AgentState.EVALUATING,
            action=ActionResult(action="scroll", target_post_id=None),
        )

        executor = LoggingExecutor()

        # Act
        with caplog.at_level(logging.INFO, logger="prism.simulation.decisions"):
            await executor.execute(agent=agent, state=state, decision=decision)

        # Assert
        log_text = caplog.records[-1].message
        entry = json.loads(log_text)

        assert "timestamp" in entry
        assert "round" in entry
        assert entry["round"] == 5
        assert "agent_id" in entry
        assert entry["agent_id"] == "test_agent"
        assert "trigger" in entry
        assert entry["trigger"] == "sees_post"
        assert "from_state" in entry
        assert entry["from_state"] == "scrolling"
        assert "to_state" in entry
        assert entry["to_state"] == "evaluating"
        assert "action_type" in entry
        assert entry["action_type"] == "scroll"

    @pytest.mark.asyncio
    async def test_writes_to_file_when_configured(self, tmp_path: Path) -> None:
        """T095: executor should write to file when log_file is configured."""
        # Arrange
        log_file = tmp_path / "decisions.jsonl"
        agent = create_mock_agent()
        state = create_test_state()

        decision = DecisionResult(
            agent_id="test_agent",
            trigger="sees_post",
            from_state=AgentState.SCROLLING,
            to_state=AgentState.EVALUATING,
            action=ActionResult(action="scroll", target_post_id=None),
        )

        executor = LoggingExecutor(log_file=log_file)

        # Act
        await executor.execute(agent=agent, state=state, decision=decision)
        executor.close()

        # Assert
        assert log_file.exists()
        content = log_file.read_text()
        lines = content.strip().split("\n")
        assert len(lines) == 1

        entry = json.loads(lines[0])
        assert entry["agent_id"] == "test_agent"
        assert entry["trigger"] == "sees_post"

    @pytest.mark.asyncio
    async def test_multiple_writes_to_file(self, tmp_path: Path) -> None:
        """executor should write multiple entries to file."""
        # Arrange
        log_file = tmp_path / "decisions.jsonl"
        agent = create_mock_agent()
        state = create_test_state()

        decision1 = DecisionResult(
            agent_id="agent1",
            trigger="sees_post",
            from_state=AgentState.SCROLLING,
            to_state=AgentState.EVALUATING,
            action=ActionResult(action="scroll", target_post_id=None),
        )

        decision2 = DecisionResult(
            agent_id="agent2",
            trigger="decides",
            from_state=AgentState.EVALUATING,
            to_state=AgentState.ENGAGING_LIKE,
            action=ActionResult(action="like", target_post_id="p1"),
        )

        executor = LoggingExecutor(log_file=log_file)

        # Act
        await executor.execute(agent=agent, state=state, decision=decision1)
        await executor.execute(agent=agent, state=state, decision=decision2)
        executor.close()

        # Assert
        content = log_file.read_text()
        lines = content.strip().split("\n")
        assert len(lines) == 2

        entry1 = json.loads(lines[0])
        entry2 = json.loads(lines[1])
        assert entry1["agent_id"] == "agent1"
        assert entry2["agent_id"] == "agent2"

    @pytest.mark.asyncio
    async def test_handles_none_action(self, caplog: pytest.LogCaptureFixture) -> None:
        """executor should handle None action gracefully."""
        # Arrange
        agent = create_mock_agent()
        state = create_test_state()

        decision = DecisionResult(
            agent_id="test_agent",
            trigger="start_browsing",
            from_state=AgentState.IDLE,
            to_state=AgentState.SCROLLING,
            action=None,
        )

        executor = LoggingExecutor()

        # Act
        with caplog.at_level(logging.INFO, logger="prism.simulation.decisions"):
            await executor.execute(agent=agent, state=state, decision=decision)

        # Assert
        log_text = caplog.records[-1].message
        entry = json.loads(log_text)
        assert entry["action_type"] is None

    @pytest.mark.asyncio
    async def test_includes_reasoner_used_field(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """executor should include reasoner_used field in log entry."""
        # Arrange
        agent = create_mock_agent()
        state = create_test_state()

        decision = DecisionResult(
            agent_id="test_agent",
            trigger="decides",
            from_state=AgentState.EVALUATING,
            to_state=AgentState.ENGAGING_LIKE,
            action=ActionResult(action="like", target_post_id="p1"),
            reasoner_used=True,
        )

        executor = LoggingExecutor()

        # Act
        with caplog.at_level(logging.INFO, logger="prism.simulation.decisions"):
            await executor.execute(agent=agent, state=state, decision=decision)

        # Assert
        log_text = caplog.records[-1].message
        entry = json.loads(log_text)
        assert entry["reasoner_used"] is True
