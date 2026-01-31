# Contract: SimulationState

## Purpose

Defines the central state container and supporting dataclasses for the simulation.

## EngagementMetrics

```python
from pydantic import BaseModel, Field


class EngagementMetrics(BaseModel):
    """Aggregated engagement metrics across all posts."""

    total_likes: int = Field(default=0, ge=0)
    total_reshares: int = Field(default=0, ge=0)
    total_replies: int = Field(default=0, ge=0)
    posts_created: int = Field(default=0, ge=0)

    def increment_like(self) -> None:
        """Increment total likes by 1."""
        self.total_likes += 1

    def increment_reshare(self) -> None:
        """Increment total reshares by 1."""
        self.total_reshares += 1

    def increment_reply(self) -> None:
        """Increment total replies by 1."""
        self.total_replies += 1

    def increment_posts(self) -> None:
        """Increment posts created by 1."""
        self.posts_created += 1
```

## SimulationState

```python
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, model_validator

from prism.rag.models import Post
from prism.statechart.statechart import Statechart
from prism.statechart.states import AgentState
from prism.statechart.queries import state_distribution

if TYPE_CHECKING:
    from prism.agents.social_agent import SocialAgent
    from prism.statechart.reasoner import StatechartReasoner


class SimulationState(BaseModel):
    """Central state container for the simulation.

    Attributes:
        round_number: Current round (0-indexed)
        posts: All posts in the simulation (initial + generated)
        agents: All agents in the simulation
        metrics: Aggregated engagement metrics
        statechart: Shared statechart definition for all agents
        reasoner: Optional LLM reasoner for ambiguous transitions
    """

    model_config = {"arbitrary_types_allowed": True}

    round_number: int = Field(default=0, ge=0)
    posts: list[Post]
    agents: list["SocialAgent"]
    metrics: EngagementMetrics = Field(default_factory=EngagementMetrics)
    statechart: Statechart
    reasoner: "StatechartReasoner | None" = None

    @model_validator(mode="after")
    def validate_agents(self) -> "SimulationState":
        """Ensure at least one agent exists."""
        if not self.agents:
            raise ValueError("simulation requires at least one agent")
        return self

    def get_post_by_id(self, post_id: str) -> Post | None:
        """Find a post by its ID."""
        for post in self.posts:
            if post.id == post_id:
                return post
        return None

    def add_post(self, post: Post) -> None:
        """Add a new post to the simulation."""
        self.posts.append(post)
        self.metrics.increment_posts()

    def get_state_distribution(self) -> dict[AgentState, int]:
        """Get current distribution of agents across states."""
        return state_distribution(self.agents)

    def advance_round(self) -> None:
        """Increment the round number."""
        self.round_number += 1
```

## DecisionResult

```python
from pydantic import BaseModel, Field

from prism.statechart.states import AgentState


class ActionResult(BaseModel):
    """Result of an action taken by an agent."""

    action_type: str  # "compose", "like", "reply", "reshare", "scroll"
    target_post_id: str | None = None
    new_post: Post | None = None
    content: str | None = None


class DecisionResult(BaseModel):
    """Result from the decision executor for one agent turn."""

    agent_id: str
    trigger: str
    from_state: AgentState
    to_state: AgentState
    action: ActionResult | None = None
    reasoner_used: bool = False
```

## RoundResult

```python
from pydantic import BaseModel

from prism.statechart.states import AgentState


class RoundResult(BaseModel):
    """Aggregated result for one simulation round."""

    round_number: int
    decisions: list[DecisionResult]
    state_distribution: dict[AgentState, int]
    duration_ms: int = 0
```

## SimulationResult

```python
from pathlib import Path

from pydantic import BaseModel

from prism.statechart.states import AgentState


class SimulationResult(BaseModel):
    """Final result after simulation completes."""

    total_rounds: int
    final_metrics: EngagementMetrics
    final_state_distribution: dict[AgentState, int]
    total_duration_ms: int = 0
    checkpoint_path: Path | None = None
```

## Usage Examples

```python
# Create initial state
state = SimulationState(
    posts=initial_posts,
    agents=agents,
    statechart=create_social_media_statechart(),
    reasoner=StatechartReasoner(client) if config.reasoner_enabled else None,
)

# Add a new post
new_post = Post(id="p100", author_id="agent_1", text="Hello world!", ...)
state.add_post(new_post)

# Check state distribution
dist = state.get_state_distribution()
# {AgentState.IDLE: 10, AgentState.SCROLLING: 5, ...}

# Advance round
state.advance_round()
assert state.round_number == 1
```
