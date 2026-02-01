"""State update executor for simulation pipeline.

This module provides the StateUpdateExecutor that applies agent actions
to simulation state, updating post engagement counts and adding new posts.
"""

from typing import TYPE_CHECKING, Any

from prism.rag.models import Post

if TYPE_CHECKING:
    from prism.rag.retriever import FeedRetriever
    from prism.simulation.results import DecisionResult
    from prism.simulation.state import SimulationState


class StateUpdateExecutor:
    """Applies agent actions to simulation state.

    Updates post engagement counts (likes, replies, reshares) and adds
    new posts to both the SimulationState and the FeedRetriever index.
    """

    def __init__(self, retriever: "FeedRetriever") -> None:
        """Initialize with a FeedRetriever for indexing new posts.

        Args:
            retriever: FeedRetriever instance for adding new posts to index.
        """
        self._retriever = retriever

    async def execute(
        self,
        agent: Any,
        state: "SimulationState",
        decision: "DecisionResult",
        new_post: Post | None = None,
    ) -> None:
        """Apply decision action to simulation state.

        Mutates state in place - updates post engagement counts and
        adds new posts as needed.

        Args:
            agent: The agent that made the decision (unused, for protocol).
            state: Current simulation state to mutate.
            decision: The decision result with action details.
            new_post: Optional new post for compose/reply/reshare actions.
        """
        action = decision.action
        if action is None:
            return

        match action.action:
            case "like":
                self._handle_like(state, action.target_post_id)
            case "reply":
                self._handle_reply(state, action.target_post_id, new_post)
            case "reshare":
                self._handle_reshare(state, action.target_post_id, new_post)
            case "compose":
                self._handle_compose(state, new_post)
            case "scroll":
                pass  # No state changes for scroll

    def _handle_like(
        self, state: "SimulationState", target_post_id: str | None
    ) -> None:
        """Handle a like action.

        Args:
            state: Simulation state to update.
            target_post_id: ID of the post to like.
        """
        if target_post_id is None:
            return

        post = state.get_post_by_id(target_post_id)
        if post:
            post.likes += 1
            state.metrics.increment_like()

    def _handle_reply(
        self,
        state: "SimulationState",
        target_post_id: str | None,
        new_post: Post | None,
    ) -> None:
        """Handle a reply action.

        Args:
            state: Simulation state to update.
            target_post_id: ID of the post being replied to.
            new_post: The reply post to add.
        """
        if target_post_id is not None:
            post = state.get_post_by_id(target_post_id)
            if post:
                post.replies += 1
                state.metrics.increment_reply()

        if new_post is not None:
            state.add_post(new_post)
            self._retriever.add_post(new_post)

    def _handle_reshare(
        self,
        state: "SimulationState",
        target_post_id: str | None,
        new_post: Post | None,
    ) -> None:
        """Handle a reshare action.

        Args:
            state: Simulation state to update.
            target_post_id: ID of the post being reshared.
            new_post: The reshare post to add.
        """
        if target_post_id is not None:
            post = state.get_post_by_id(target_post_id)
            if post:
                post.reshares += 1
                state.metrics.increment_reshare()

        if new_post is not None:
            state.add_post(new_post)
            self._retriever.add_post(new_post)

    def _handle_compose(
        self,
        state: "SimulationState",
        new_post: Post | None,
    ) -> None:
        """Handle a compose action.

        Args:
            state: Simulation state to update.
            new_post: The new post to add.
        """
        if new_post is not None:
            state.add_post(new_post)
            self._retriever.add_post(new_post)
