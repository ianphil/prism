"""Simulation state models.

This module defines the core state models for simulation execution including
EngagementMetrics for tracking cumulative engagement and SimulationState
as the single source of truth during simulation.

Type Safety Note:
    The agents and reasoner fields use Any at runtime for Pydantic compatibility,
    but are expected to conform to SocialAgentProtocol and StatechartReasonerProtocol
    respectively. See prism.simulation.protocols for the expected interfaces.
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator

from prism.rag.models import Post
from prism.statechart.queries import state_distribution
from prism.statechart.statechart import Statechart
from prism.statechart.states import AgentState


class EngagementMetrics(BaseModel):
    """Cumulative engagement metrics for simulation analysis.

    Tracks total likes, reshares, replies, and posts created across
    all agents during the simulation. All fields have ge=0 constraint.

    Attributes:
        total_likes: Cumulative number of likes.
        total_reshares: Cumulative number of reshares.
        total_replies: Cumulative number of replies.
        posts_created: Number of posts created during simulation.
    """

    total_likes: int = Field(default=0, ge=0)
    total_reshares: int = Field(default=0, ge=0)
    total_replies: int = Field(default=0, ge=0)
    posts_created: int = Field(default=0, ge=0)

    def increment_like(self) -> None:
        """Increment total_likes by 1."""
        self.total_likes += 1

    def increment_reshare(self) -> None:
        """Increment total_reshares by 1."""
        self.total_reshares += 1

    def increment_reply(self) -> None:
        """Increment total_replies by 1."""
        self.total_replies += 1

    def increment_post_created(self) -> None:
        """Increment posts_created by 1."""
        self.posts_created += 1


class SimulationState(BaseModel):
    """Single source of truth for simulation execution.

    Contains all data needed by executors including posts, agents,
    the statechart definition, and cumulative metrics.

    Attributes:
        posts: List of posts in the simulation feed.
        agents: List of agents participating in simulation (must be non-empty).
        round_number: Current simulation round (0-indexed).
        metrics: Cumulative engagement metrics.
        statechart: Statechart definition for agent behavior.
        reasoner: Optional LLM reasoner for ambiguous state transitions.
    """

    model_config = {"arbitrary_types_allowed": True}

    posts: list[Post] = Field(default_factory=list)
    agents: list[Any] = Field(default_factory=list)
    round_number: int = Field(default=0)
    metrics: EngagementMetrics = Field(default_factory=EngagementMetrics)
    statechart: Statechart
    reasoner: Any = None

    @field_validator("agents")
    @classmethod
    def validate_agents_not_empty(cls, v: list[Any]) -> list[Any]:
        """Validate that agents list is not empty.

        Args:
            v: The agents list to validate.

        Returns:
            The validated agents list.

        Raises:
            ValueError: If agents list is empty.
        """
        if not v:
            raise ValueError("agents list must not be empty")
        return v

    def get_state_distribution(self) -> dict[AgentState, int]:
        """Get distribution of agents across states.

        Delegates to the existing state_distribution function from
        prism.statechart.queries.

        Returns:
            Dictionary mapping AgentState to count of agents in that state.
        """
        return state_distribution(self.agents)

    def get_post_by_id(self, post_id: str) -> Post | None:
        """Find a post by its ID.

        Args:
            post_id: The ID of the post to find.

        Returns:
            The Post if found, None otherwise.
        """
        for post in self.posts:
            if post.id == post_id:
                return post
        return None

    def add_post(self, post: Post) -> None:
        """Add a post to the simulation and increment posts_created.

        Args:
            post: The post to add to the simulation.
        """
        self.posts.append(post)
        self.metrics.increment_post_created()

    def advance_round(self) -> None:
        """Increment round_number by 1."""
        self.round_number += 1
