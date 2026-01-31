"""Simulation state checkpointing.

This module provides the Checkpointer class for saving and loading
simulation state to/from JSON checkpoint files with atomic writes.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, overload

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from prism.simulation.protocols import SocialAgentProtocol
    from prism.simulation.state import SimulationState
    from prism.statechart.statechart import Statechart

    # Type alias for agent reconstruction factory
    AgentFactory = Callable[[dict[str, Any]], SocialAgentProtocol]


class CheckpointData(BaseModel):
    """Serializable snapshot of simulation state.

    This is the JSON-serializable representation used for checkpoint files.
    Note: Statechart and Reasoner are not serialized - they must be
    reconstructed from configuration on load.

    Attributes:
        version: Checkpoint format version for compatibility checking.
        round_number: Round number at checkpoint time.
        posts: Serialized Post objects as dicts.
        agents: Serialized agent state as dicts.
        metrics: EngagementMetrics as dict.
        state_distribution: Distribution of agents across states (state.value -> count).
        timestamp: ISO timestamp of checkpoint creation.
    """

    version: str = Field(default="1.0", description="Checkpoint format version")
    round_number: int = Field(ge=0)
    posts: list[dict[str, Any]] = Field(description="Serialized Post objects")
    agents: list[dict[str, Any]] = Field(description="Serialized agent state")
    metrics: dict[str, int] = Field(description="EngagementMetrics as dict")
    state_distribution: dict[str, int] = Field(
        description="State distribution (state.value -> count)"
    )
    timestamp: str = Field(description="ISO timestamp of checkpoint creation")


class Checkpointer:
    """Saves and loads simulation state checkpoints.

    Uses atomic write pattern (temp file + rename) to prevent
    checkpoint corruption from interrupted writes.
    """

    SUPPORTED_VERSIONS = {"1.0"}

    def __init__(self, checkpoint_dir: Path) -> None:
        """Initialize with checkpoint directory.

        Creates the directory if it doesn't exist.

        Args:
            checkpoint_dir: Directory to save/load checkpoints.
        """
        self._dir = checkpoint_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def save(self, state: "SimulationState") -> Path:
        """Save simulation state to checkpoint file.

        Uses atomic write via temp file + rename to prevent corruption.

        Args:
            state: Current simulation state to save.

        Returns:
            Path to the saved checkpoint file.
        """
        # Build checkpoint data
        checkpoint = CheckpointData(
            version="1.0",
            round_number=state.round_number,
            posts=[self._serialize_post(p) for p in state.posts],
            agents=[self._serialize_agent(a) for a in state.agents],
            metrics={
                "total_likes": state.metrics.total_likes,
                "total_reshares": state.metrics.total_reshares,
                "total_replies": state.metrics.total_replies,
                "posts_created": state.metrics.posts_created,
            },
            state_distribution={
                s.value: c for s, c in state.get_state_distribution().items()
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        # File naming with zero-padded round number
        filename = f"checkpoint_round_{state.round_number:04d}.json"
        path = self._dir / filename

        # Atomic write via temp file
        temp_path = path.with_suffix(".tmp")
        with open(temp_path, "w") as f:
            json.dump(checkpoint.model_dump(), f, indent=2)
        temp_path.rename(path)

        return path

    @overload
    def load(
        self,
        path: Path,
        statechart: "Statechart",
        reasoner: Any = None,
        *,
        agent_factory: "AgentFactory",
    ) -> "SimulationState": ...

    @overload
    def load(
        self,
        path: Path,
        statechart: "Statechart",
        reasoner: Any = None,
        agent_factory: None = None,
    ) -> "SimulationState": ...

    def load(
        self,
        path: Path,
        statechart: "Statechart",
        reasoner: Any = None,
        agent_factory: "AgentFactory | None" = None,
    ) -> "SimulationState":
        """Load simulation state from checkpoint file.

        Args:
            path: Path to checkpoint JSON file.
            statechart: Statechart to use (not serialized in checkpoint).
            reasoner: Optional reasoner to use (not serialized in checkpoint).
            agent_factory: Optional callable to reconstruct agents from dicts.
                If provided, returns SimulationState with SocialAgentProtocol agents.
                If None, agents are stored as raw dicts (for testing or deferred
                reconstruction).

        Returns:
            Reconstructed SimulationState. Agent types depend on agent_factory:
            - With agent_factory: agents are SocialAgentProtocol instances
            - Without agent_factory: agents are raw dict objects

        Raises:
            ValueError: If checkpoint version is not supported.
        """
        from prism.rag.models import Post
        from prism.simulation.state import EngagementMetrics, SimulationState

        with open(path) as f:
            data = json.load(f)

        # Version check
        version = data.get("version", "unknown")
        if version not in self.SUPPORTED_VERSIONS:
            raise ValueError(f"Unsupported checkpoint version: {version}")

        # Reconstruct posts
        posts = [Post(**p) for p in data["posts"]]

        # Reconstruct agents
        if agent_factory:
            agents = [agent_factory(a) for a in data["agents"]]
        else:
            # Return agent dicts as-is (for testing or deferred reconstruction)
            agents = data["agents"]

        # Reconstruct metrics
        metrics = EngagementMetrics(**data["metrics"])

        return SimulationState(
            round_number=data["round_number"],
            posts=posts,
            agents=agents,
            metrics=metrics,
            statechart=statechart,
            reasoner=reasoner,
        )

    def _serialize_post(self, post: Any) -> dict:
        """Serialize Post to dict.

        Args:
            post: Post object to serialize.

        Returns:
            Dictionary representation of the post.
        """
        return post.model_dump(mode="json")

    def _serialize_agent(self, agent: Any) -> dict:
        """Serialize agent state to dict.

        Only serializes restorable state, not the full agent object.

        Args:
            agent: Agent object to serialize.

        Returns:
            Dictionary with agent state data.
        """
        return {
            "agent_id": agent.agent_id,
            "name": agent.name,
            "interests": agent.interests,
            "personality": agent.personality,
            "state": agent.state.value,
            "ticks_in_state": agent.ticks_in_state,
            "engagement_threshold": agent.engagement_threshold,
        }

    def latest_checkpoint(self) -> Path | None:
        """Find the most recent checkpoint in the directory.

        Returns:
            Path to latest checkpoint, or None if no checkpoints exist.
        """
        checkpoints = sorted(self._dir.glob("checkpoint_round_*.json"))
        return checkpoints[-1] if checkpoints else None

    def checkpoint_for_round(self, round_number: int) -> Path | None:
        """Find checkpoint for a specific round.

        Args:
            round_number: The round number to find checkpoint for.

        Returns:
            Path to checkpoint, or None if not found.
        """
        filename = f"checkpoint_round_{round_number:04d}.json"
        path = self._dir / filename
        return path if path.exists() else None
