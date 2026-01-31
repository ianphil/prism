"""Feed retrieval executor for simulation pipeline.

This module provides the FeedRetrievalExecutor that retrieves feed posts
for an agent using the FeedRetriever.
"""

from typing import TYPE_CHECKING, Any

from prism.rag.models import Post

if TYPE_CHECKING:
    from prism.rag.retriever import FeedRetriever
    from prism.simulation.state import SimulationState


class FeedRetrievalExecutor:
    """Retrieves feed posts for an agent.

    Wraps FeedRetriever.get_feed() in the executor interface, using
    the agent's interests for preference-based retrieval.
    """

    def __init__(self, retriever: "FeedRetriever") -> None:
        """Initialize with a FeedRetriever.

        Args:
            retriever: FeedRetriever instance for feed queries.
        """
        self._retriever = retriever

    def execute(
        self,
        agent: Any,
        state: "SimulationState",
    ) -> list[Post]:
        """Retrieve feed for the agent based on their interests.

        Args:
            agent: The agent to retrieve feed for (must have .interests).
            state: Current simulation state (unused, for protocol compliance).

        Returns:
            List of Post objects (up to feed_size configured in retriever).
        """
        return self._retriever.get_feed(interests=agent.interests)

    async def execute_async(
        self,
        agent: Any,
        state: "SimulationState",
    ) -> list[Post]:
        """Async version of execute for pipeline compatibility.

        Currently delegates to sync version since FeedRetriever is sync.

        Args:
            agent: The agent to retrieve feed for.
            state: Current simulation state.

        Returns:
            List of Post objects.
        """
        return self.execute(agent, state)
