# XAlgorithmRanker Contract

## Overview

Main ranking component that implements X's heuristic rescoring pipeline. Wraps `FeedRetriever` for base score computation and applies documented scale factors.

## Interface

```python
from typing import TYPE_CHECKING

from prism.rag.config import RankingConfig
from prism.rag.models import Post

if TYPE_CHECKING:
    from prism.agents.social_agent import SocialAgent
    from prism.rag.retriever import FeedRetriever
    from prism.simulation.protocols import SocialGraphProtocol

class XAlgorithmRanker:
    """X algorithm ranking pipeline with heuristic rescoring."""

    def __init__(
        self,
        retriever: "FeedRetriever",
        config: RankingConfig,
    ) -> None:
        """Initialize ranker with retriever and configuration.

        Args:
            retriever: FeedRetriever for ChromaDB queries.
            config: RankingConfig with scale factors.
        """
        ...

    def get_feed(
        self,
        agent: "SocialAgent",
        social_graph: "SocialGraphProtocol",
    ) -> list[Post]:
        """Generate ranked feed for an agent.

        Implements the full ranking pipeline:
        1. Source in-network candidates (from followed authors)
        2. Source out-of-network candidates (from similarity search)
        3. Compute base scores from embedding similarity
        4. Apply heuristic rescoring (OON, reply, author diversity)
        5. Sort by final score and return top N

        Args:
            agent: The agent to generate feed for.
            social_graph: Social graph for follow relationship queries.

        Returns:
            List of Post objects, ranked by final score.
            Length is min(feed_size, available candidates).
        """
        ...

    def _get_in_network_candidates(
        self,
        agent: "SocialAgent",
        following: set[str],
    ) -> list[tuple[Post, float]]:
        """Get candidates from followed authors.

        Args:
            agent: The requesting agent.
            following: Set of agent IDs the agent follows.

        Returns:
            List of (Post, similarity_score) tuples.
        """
        ...

    def _get_out_of_network_candidates(
        self,
        agent: "SocialAgent",
        following: set[str],
    ) -> list[tuple[Post, float]]:
        """Get candidates via similarity search, excluding followed authors.

        Args:
            agent: The requesting agent.
            following: Set of agent IDs to exclude.

        Returns:
            List of (Post, similarity_score) tuples.
        """
        ...

    def _apply_heuristic_rescoring(
        self,
        candidates: list["RankedCandidate"],
    ) -> list["RankedCandidate"]:
        """Apply scale factors and author diversity.

        Modifies candidates in place with final_score.

        Args:
            candidates: List of RankedCandidate with base scores.

        Returns:
            Same list with final_score computed.
        """
        ...
```

## RankedCandidate Internal Model

```python
from dataclasses import dataclass, field

@dataclass
class RankedCandidate:
    """Internal model for ranking pipeline."""

    post: Post
    base_score: float
    is_in_network: bool
    is_reply: bool
    author_occurrence: int = 0
    final_score: float = field(init=False)

    def __post_init__(self) -> None:
        self.final_score = self.base_score
```

## Rescoring Formula

```python
def compute_final_score(
    base_score: float,
    is_in_network: bool,
    is_reply: bool,
    author_occurrence: int,
    config: RankingConfig,
) -> float:
    """Compute final score with all scale factors."""
    score = base_score

    # Out-of-network penalty
    if not is_in_network:
        score *= config.out_of_network_scale

    # Reply penalty
    if is_reply:
        score *= config.reply_scale

    # Author diversity decay (only for repeat authors)
    if author_occurrence > 0:
        decay = max(
            config.author_diversity_floor,
            config.author_diversity_decay ** author_occurrence,
        )
        score *= decay

    return score
```

## Mode Delegation

When `config.mode` is not `x_algo`, the ranker delegates to simpler paths:

```python
def get_feed(self, agent, social_graph) -> list[Post]:
    if self._config.mode == "preference":
        return self._retriever.get_feed(
            interests=agent.interests,
            mode="preference",
        )
    elif self._config.mode == "random":
        return self._retriever.get_feed(mode="random")
    else:  # x_algo
        return self._get_feed_x_algo(agent, social_graph)
```

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Empty following set | All candidates treated as OON |
| No candidates found | Return empty list |
| ChromaDB error | Propagate exception |
| Agent has no interests | Use empty query (random-ish) |
