# Contract: Checkpointer

## Purpose

Defines the checkpoint serialization format and save/load operations for simulation state.

## CheckpointData Schema

```python
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CheckpointData(BaseModel):
    """Serializable snapshot of simulation state.

    This is the JSON-serializable representation used for save/load.
    Note: Statechart and Reasoner are not serialized - they are
    reconstructed from configuration on load.
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
```

## JSON Format

```json
{
  "version": "1.0",
  "round_number": 25,
  "posts": [
    {
      "id": "p001",
      "author_id": "agent_1",
      "text": "Hello world!",
      "timestamp": "2026-01-30T10:00:00Z",
      "has_media": false,
      "media_type": null,
      "media_description": null,
      "likes": 5,
      "reshares": 2,
      "replies": 1,
      "velocity": 0.5
    }
  ],
  "agents": [
    {
      "agent_id": "agent_1",
      "name": "Alice",
      "interests": ["technology", "crypto"],
      "personality": "curious and enthusiastic",
      "state": "scrolling",
      "ticks_in_state": 2,
      "engagement_threshold": 0.5
    }
  ],
  "metrics": {
    "total_likes": 150,
    "total_reshares": 45,
    "total_replies": 30,
    "posts_created": 20
  },
  "state_distribution": {
    "idle": 10,
    "scrolling": 35,
    "evaluating": 5,
    "composing": 2,
    "engaging_like": 3,
    "engaging_reply": 2,
    "engaging_reshare": 1,
    "resting": 2
  },
  "timestamp": "2026-01-30T12:30:45.123456Z"
}
```

## Checkpointer Class

```python
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from prism.rag.models import Post
from prism.statechart.states import AgentState

if TYPE_CHECKING:
    from prism.simulation.state import SimulationState
    from prism.agents.social_agent import SocialAgent
    from agent_framework.ollama import OllamaChatClient


class Checkpointer:
    """Saves and loads simulation state checkpoints."""

    SUPPORTED_VERSIONS = {"1.0"}

    def __init__(self, checkpoint_dir: Path) -> None:
        """Initialize with checkpoint directory.

        Args:
            checkpoint_dir: Directory to save/load checkpoints.
                           Created if it doesn't exist.
        """
        self._dir = checkpoint_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def save(self, state: "SimulationState") -> Path:
        """Save simulation state to checkpoint file.

        Args:
            state: Current simulation state

        Returns:
            Path to the saved checkpoint file
        """
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

        filename = f"checkpoint_round_{state.round_number:04d}.json"
        path = self._dir / filename

        # Atomic write via temp file
        temp_path = path.with_suffix(".tmp")
        with open(temp_path, "w") as f:
            json.dump(checkpoint.model_dump(), f, indent=2)
        temp_path.rename(path)

        return path

    def load(
        self,
        path: Path,
        client: "OllamaChatClient",
        statechart: "Statechart",
        reasoner: "StatechartReasoner | None",
    ) -> "SimulationState":
        """Load simulation state from checkpoint file.

        Args:
            path: Path to checkpoint JSON file
            client: LLM client for reconstructing agents
            statechart: Statechart to use (not serialized)
            reasoner: Reasoner to use (not serialized)

        Returns:
            Reconstructed SimulationState

        Raises:
            ValueError: If checkpoint version is not supported
        """
        with open(path) as f:
            data = json.load(f)

        version = data.get("version", "unknown")
        if version not in self.SUPPORTED_VERSIONS:
            raise ValueError(f"Unsupported checkpoint version: {version}")

        # Reconstruct posts
        posts = [self._deserialize_post(p) for p in data["posts"]]

        # Reconstruct agents
        agents = [
            self._deserialize_agent(a, client)
            for a in data["agents"]
        ]

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

    def _serialize_post(self, post: Post) -> dict:
        """Serialize Post to dict."""
        return post.model_dump(mode="json")

    def _deserialize_post(self, data: dict) -> Post:
        """Deserialize dict to Post."""
        return Post(**data)

    def _serialize_agent(self, agent: "SocialAgent") -> dict:
        """Serialize agent state (not full agent, just restorable state)."""
        return {
            "agent_id": agent.agent_id,
            "name": agent.name,
            "interests": agent.interests,
            "personality": agent.personality,
            "state": agent.state.value,
            "ticks_in_state": agent.ticks_in_state,
            "engagement_threshold": agent.engagement_threshold,
        }

    def _deserialize_agent(
        self,
        data: dict,
        client: "OllamaChatClient",
    ) -> "SocialAgent":
        """Deserialize agent from checkpoint data."""
        from prism.agents.social_agent import SocialAgent

        agent = SocialAgent(
            agent_id=data["agent_id"],
            name=data["name"],
            interests=data["interests"],
            personality=data["personality"],
            client=client,
            engagement_threshold=data.get("engagement_threshold", 0.5),
        )

        # Restore state
        agent.state = AgentState(data["state"])
        agent.ticks_in_state = data.get("ticks_in_state", 0)

        return agent

    def latest_checkpoint(self) -> Path | None:
        """Find the most recent checkpoint in the directory.

        Returns:
            Path to latest checkpoint, or None if no checkpoints exist
        """
        checkpoints = sorted(self._dir.glob("checkpoint_round_*.json"))
        return checkpoints[-1] if checkpoints else None

    def checkpoint_for_round(self, round_number: int) -> Path | None:
        """Find checkpoint for a specific round.

        Returns:
            Path to checkpoint, or None if not found
        """
        filename = f"checkpoint_round_{round_number:04d}.json"
        path = self._dir / filename
        return path if path.exists() else None
```

## Usage Examples

```python
# Save checkpoint
checkpointer = Checkpointer(Path("outputs/checkpoints"))
checkpoint_path = checkpointer.save(state)
# outputs/checkpoints/checkpoint_round_0025.json

# Load checkpoint
state = checkpointer.load(
    path=checkpoint_path,
    client=ollama_client,
    statechart=create_social_media_statechart(),
    reasoner=StatechartReasoner(client) if config.reasoner_enabled else None,
)

# Find latest checkpoint for resume
latest = checkpointer.latest_checkpoint()
if latest:
    state = checkpointer.load(latest, client, statechart, reasoner)
```

## File Naming Convention

Checkpoints use zero-padded round numbers for correct sorting:

```
checkpoint_round_0000.json  # Round 0
checkpoint_round_0001.json  # Round 1
...
checkpoint_round_0100.json  # Round 100
```

## Atomic Write Safety

Checkpoints are written atomically using a temporary file:

1. Write to `checkpoint_round_NNNN.tmp`
2. Rename to `checkpoint_round_NNNN.json`

This prevents corruption if the process is killed during write.
