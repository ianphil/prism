"""Tests for simulation checkpointer.

This module tests the Checkpointer class for saving and loading
simulation state to/from JSON checkpoint files.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from prism.rag.models import Post
from prism.simulation.checkpointer import CheckpointData, Checkpointer
from prism.simulation.state import EngagementMetrics, SimulationState
from prism.simulation.statechart_factory import create_social_media_statechart
from prism.statechart.states import AgentState


def create_mock_agent(
    agent_id: str = "agent_1",
    name: str = "Alice",
    state: AgentState = AgentState.SCROLLING,
    ticks_in_state: int = 2,
    engagement_threshold: float = 0.5,
) -> MagicMock:
    """Create a mock agent for testing."""
    agent = MagicMock()
    agent.agent_id = agent_id
    agent.name = name
    agent.state = state
    agent.ticks_in_state = ticks_in_state
    agent.interests = ["technology", "science"]
    agent.personality = "curious"
    agent.engagement_threshold = engagement_threshold
    return agent


def create_test_post(post_id: str = "post_1") -> Post:
    """Create a test post for testing."""
    return Post(
        id=post_id,
        author_id="author_1",
        text="Test post content",
        timestamp=datetime.now(timezone.utc),
        likes=5,
        reshares=2,
        replies=1,
    )


class TestCheckpointerSave:
    """Tests for Checkpointer.save method."""

    def test_save_creates_json_file(self, tmp_path: Path) -> None:
        """T101: Checkpointer.save creates JSON file."""
        # Arrange
        checkpoint_dir = tmp_path / "checkpoints"
        checkpointer = Checkpointer(checkpoint_dir)
        agent = create_mock_agent()
        post = create_test_post()
        statechart = create_social_media_statechart()

        state = SimulationState(
            posts=[post],
            agents=[agent],
            statechart=statechart,
            round_number=5,
        )

        # Act
        saved_path = checkpointer.save(state)

        # Assert
        assert saved_path.exists()
        assert saved_path.suffix == ".json"

        # Verify it's valid JSON
        with open(saved_path) as f:
            data = json.load(f)
        assert "round_number" in data
        assert data["round_number"] == 5

    def test_saved_file_includes_version_field(self, tmp_path: Path) -> None:
        """T103: Saved file includes version field."""
        # Arrange
        checkpoint_dir = tmp_path / "checkpoints"
        checkpointer = Checkpointer(checkpoint_dir)
        agent = create_mock_agent()
        statechart = create_social_media_statechart()

        state = SimulationState(
            posts=[],
            agents=[agent],
            statechart=statechart,
        )

        # Act
        saved_path = checkpointer.save(state)

        # Assert
        with open(saved_path) as f:
            data = json.load(f)
        assert "version" in data
        assert data["version"] == "1.0"

    def test_file_path_includes_round_number(self, tmp_path: Path) -> None:
        """T105: File path includes round number."""
        # Arrange
        checkpoint_dir = tmp_path / "checkpoints"
        checkpointer = Checkpointer(checkpoint_dir)
        agent = create_mock_agent()
        statechart = create_social_media_statechart()

        state = SimulationState(
            posts=[],
            agents=[agent],
            statechart=statechart,
            round_number=25,
        )

        # Act
        saved_path = checkpointer.save(state)

        # Assert
        assert "0025" in saved_path.name
        assert saved_path.name == "checkpoint_round_0025.json"

    def test_atomic_write_uses_temp_file(self, tmp_path: Path) -> None:
        """T107: Atomic write uses temp file pattern."""
        # Arrange
        checkpoint_dir = tmp_path / "checkpoints"
        checkpointer = Checkpointer(checkpoint_dir)
        agent = create_mock_agent()
        statechart = create_social_media_statechart()

        state = SimulationState(
            posts=[],
            agents=[agent],
            statechart=statechart,
            round_number=10,
        )

        # Act
        saved_path = checkpointer.save(state)

        # Assert - no .tmp file should remain after save
        tmp_files = list(checkpoint_dir.glob("*.tmp"))
        assert len(tmp_files) == 0

        # The final file should exist
        assert saved_path.exists()

    def test_save_includes_posts_data(self, tmp_path: Path) -> None:
        """Verify posts are serialized correctly."""
        # Arrange
        checkpoint_dir = tmp_path / "checkpoints"
        checkpointer = Checkpointer(checkpoint_dir)
        agent = create_mock_agent()
        post = create_test_post("test_post_123")
        statechart = create_social_media_statechart()

        state = SimulationState(
            posts=[post],
            agents=[agent],
            statechart=statechart,
        )

        # Act
        saved_path = checkpointer.save(state)

        # Assert
        with open(saved_path) as f:
            data = json.load(f)
        assert "posts" in data
        assert len(data["posts"]) == 1
        assert data["posts"][0]["id"] == "test_post_123"

    def test_save_includes_agents_data(self, tmp_path: Path) -> None:
        """Verify agents are serialized correctly."""
        # Arrange
        checkpoint_dir = tmp_path / "checkpoints"
        checkpointer = Checkpointer(checkpoint_dir)
        agent = create_mock_agent(agent_id="agent_42", state=AgentState.EVALUATING)
        statechart = create_social_media_statechart()

        state = SimulationState(
            posts=[],
            agents=[agent],
            statechart=statechart,
        )

        # Act
        saved_path = checkpointer.save(state)

        # Assert
        with open(saved_path) as f:
            data = json.load(f)
        assert "agents" in data
        assert len(data["agents"]) == 1
        assert data["agents"][0]["agent_id"] == "agent_42"
        assert data["agents"][0]["state"] == "evaluating"

    def test_save_includes_metrics(self, tmp_path: Path) -> None:
        """Verify metrics are serialized correctly."""
        # Arrange
        checkpoint_dir = tmp_path / "checkpoints"
        checkpointer = Checkpointer(checkpoint_dir)
        agent = create_mock_agent()
        statechart = create_social_media_statechart()

        metrics = EngagementMetrics(
            total_likes=100,
            total_reshares=50,
            total_replies=25,
            posts_created=10,
        )
        state = SimulationState(
            posts=[],
            agents=[agent],
            statechart=statechart,
            metrics=metrics,
        )

        # Act
        saved_path = checkpointer.save(state)

        # Assert
        with open(saved_path) as f:
            data = json.load(f)
        assert data["metrics"]["total_likes"] == 100
        assert data["metrics"]["total_reshares"] == 50
        assert data["metrics"]["total_replies"] == 25
        assert data["metrics"]["posts_created"] == 10

    def test_save_includes_state_distribution(self, tmp_path: Path) -> None:
        """Verify state distribution is serialized correctly."""
        # Arrange
        checkpoint_dir = tmp_path / "checkpoints"
        checkpointer = Checkpointer(checkpoint_dir)
        agent1 = create_mock_agent(agent_id="a1", state=AgentState.SCROLLING)
        agent2 = create_mock_agent(agent_id="a2", state=AgentState.SCROLLING)
        agent3 = create_mock_agent(agent_id="a3", state=AgentState.IDLE)
        statechart = create_social_media_statechart()

        state = SimulationState(
            posts=[],
            agents=[agent1, agent2, agent3],
            statechart=statechart,
        )

        # Act
        saved_path = checkpointer.save(state)

        # Assert
        with open(saved_path) as f:
            data = json.load(f)
        assert "state_distribution" in data
        assert data["state_distribution"]["scrolling"] == 2
        assert data["state_distribution"]["idle"] == 1

    def test_save_includes_timestamp(self, tmp_path: Path) -> None:
        """Verify timestamp is included in checkpoint."""
        # Arrange
        checkpoint_dir = tmp_path / "checkpoints"
        checkpointer = Checkpointer(checkpoint_dir)
        agent = create_mock_agent()
        statechart = create_social_media_statechart()

        state = SimulationState(
            posts=[],
            agents=[agent],
            statechart=statechart,
        )

        # Act
        saved_path = checkpointer.save(state)

        # Assert
        with open(saved_path) as f:
            data = json.load(f)
        assert "timestamp" in data
        # Should be ISO format
        assert "T" in data["timestamp"]

    def test_creates_checkpoint_dir_if_not_exists(self, tmp_path: Path) -> None:
        """Verify checkpoint directory is created if needed."""
        # Arrange
        checkpoint_dir = tmp_path / "nested" / "checkpoints"
        assert not checkpoint_dir.exists()

        checkpointer = Checkpointer(checkpoint_dir)
        agent = create_mock_agent()
        statechart = create_social_media_statechart()

        state = SimulationState(
            posts=[],
            agents=[agent],
            statechart=statechart,
        )

        # Act
        saved_path = checkpointer.save(state)

        # Assert
        assert checkpoint_dir.exists()
        assert saved_path.exists()


class TestCheckpointerLoad:
    """Tests for Checkpointer.load method."""

    def test_load_reconstructs_state(self, tmp_path: Path) -> None:
        """T109: Checkpointer.load reconstructs state."""
        # Arrange - save a checkpoint first
        checkpoint_dir = tmp_path / "checkpoints"
        checkpointer = Checkpointer(checkpoint_dir)
        agent = create_mock_agent()
        post = create_test_post()
        statechart = create_social_media_statechart()

        original_state = SimulationState(
            posts=[post],
            agents=[agent],
            statechart=statechart,
            round_number=10,
        )
        original_state.metrics.total_likes = 50
        saved_path = checkpointer.save(original_state)

        # Act - load it back
        loaded_state = checkpointer.load(
            path=saved_path,
            statechart=statechart,
        )

        # Assert
        assert loaded_state.round_number == 10
        assert len(loaded_state.posts) == 1
        assert loaded_state.posts[0].id == post.id
        assert loaded_state.metrics.total_likes == 50

    def test_load_validates_version(self, tmp_path: Path) -> None:
        """T111: load validates version."""
        # Arrange - write a checkpoint with invalid version
        checkpoint_dir = tmp_path / "checkpoints"
        checkpoint_dir.mkdir(parents=True)
        checkpointer = Checkpointer(checkpoint_dir)

        bad_checkpoint = {
            "version": "99.0",  # Unsupported version
            "round_number": 5,
            "posts": [],
            "agents": [{"agent_id": "a1", "state": "idle"}],
            "metrics": {
                "total_likes": 0,
                "total_reshares": 0,
                "total_replies": 0,
                "posts_created": 0,
            },
            "state_distribution": {},
            "timestamp": "2026-01-30T12:00:00Z",
        }
        bad_path = checkpoint_dir / "checkpoint_round_0005.json"
        with open(bad_path, "w") as f:
            json.dump(bad_checkpoint, f)

        statechart = create_social_media_statechart()

        # Act & Assert
        with pytest.raises(ValueError, match="Unsupported checkpoint version"):
            checkpointer.load(path=bad_path, statechart=statechart)

    def test_load_with_valid_version(self, tmp_path: Path) -> None:
        """T112: Version check passes for supported versions."""
        # Arrange
        checkpoint_dir = tmp_path / "checkpoints"
        checkpoint_dir.mkdir(parents=True)
        checkpointer = Checkpointer(checkpoint_dir)

        valid_checkpoint = {
            "version": "1.0",
            "round_number": 5,
            "posts": [],
            "agents": [{"agent_id": "a1", "state": "idle"}],
            "metrics": {
                "total_likes": 10,
                "total_reshares": 5,
                "total_replies": 2,
                "posts_created": 1,
            },
            "state_distribution": {"idle": 1},
            "timestamp": "2026-01-30T12:00:00Z",
        }
        valid_path = checkpoint_dir / "checkpoint_round_0005.json"
        with open(valid_path, "w") as f:
            json.dump(valid_checkpoint, f)

        statechart = create_social_media_statechart()

        # Act
        loaded_state = checkpointer.load(path=valid_path, statechart=statechart)

        # Assert
        assert loaded_state.round_number == 5
        assert loaded_state.metrics.total_likes == 10


class TestCheckpointerFinders:
    """Tests for Checkpointer.latest_checkpoint and checkpoint_for_round."""

    def test_latest_checkpoint_finds_most_recent(self, tmp_path: Path) -> None:
        """T113: latest_checkpoint finds most recent."""
        # Arrange
        checkpoint_dir = tmp_path / "checkpoints"
        checkpointer = Checkpointer(checkpoint_dir)
        agent = create_mock_agent()
        statechart = create_social_media_statechart()

        # Save multiple checkpoints
        for round_num in [5, 10, 3, 8]:
            state = SimulationState(
                posts=[],
                agents=[agent],
                statechart=statechart,
                round_number=round_num,
            )
            checkpointer.save(state)

        # Act
        latest = checkpointer.latest_checkpoint()

        # Assert - should find round 10 (highest number, sorts last)
        assert latest is not None
        assert "0010" in latest.name

    def test_latest_checkpoint_returns_none_when_empty(self, tmp_path: Path) -> None:
        """T114: latest_checkpoint returns None for empty directory."""
        # Arrange
        checkpoint_dir = tmp_path / "checkpoints"
        checkpointer = Checkpointer(checkpoint_dir)

        # Act
        latest = checkpointer.latest_checkpoint()

        # Assert
        assert latest is None

    def test_checkpoint_for_round_finds_specific_round(self, tmp_path: Path) -> None:
        """T115: checkpoint_for_round finds specific round."""
        # Arrange
        checkpoint_dir = tmp_path / "checkpoints"
        checkpointer = Checkpointer(checkpoint_dir)
        agent = create_mock_agent()
        statechart = create_social_media_statechart()

        # Save checkpoints for rounds 5 and 10
        for round_num in [5, 10]:
            state = SimulationState(
                posts=[],
                agents=[agent],
                statechart=statechart,
                round_number=round_num,
            )
            checkpointer.save(state)

        # Act
        found = checkpointer.checkpoint_for_round(5)

        # Assert
        assert found is not None
        assert "0005" in found.name

    def test_checkpoint_for_round_returns_none_when_not_found(
        self, tmp_path: Path
    ) -> None:
        """T116: checkpoint_for_round returns None when not found."""
        # Arrange
        checkpoint_dir = tmp_path / "checkpoints"
        checkpointer = Checkpointer(checkpoint_dir)
        agent = create_mock_agent()
        statechart = create_social_media_statechart()

        # Save only round 5
        state = SimulationState(
            posts=[],
            agents=[agent],
            statechart=statechart,
            round_number=5,
        )
        checkpointer.save(state)

        # Act
        found = checkpointer.checkpoint_for_round(99)

        # Assert
        assert found is None


class TestCheckpointData:
    """Tests for CheckpointData model."""

    def test_checkpoint_data_has_version_default(self) -> None:
        """T104: CheckpointData has version field with default."""
        # Act
        checkpoint = CheckpointData(
            round_number=0,
            posts=[],
            agents=[],
            metrics={},
            state_distribution={},
            timestamp="2026-01-30T12:00:00Z",
        )

        # Assert
        assert checkpoint.version == "1.0"

    def test_checkpoint_data_serializable(self) -> None:
        """Verify CheckpointData is JSON serializable."""
        # Arrange
        checkpoint = CheckpointData(
            version="1.0",
            round_number=10,
            posts=[{"id": "p1", "text": "hello"}],
            agents=[{"agent_id": "a1", "state": "idle"}],
            metrics={"total_likes": 5},
            state_distribution={"idle": 1},
            timestamp="2026-01-30T12:00:00Z",
        )

        # Act
        json_str = checkpoint.model_dump_json()

        # Assert
        data = json.loads(json_str)
        assert data["version"] == "1.0"
        assert data["round_number"] == 10
