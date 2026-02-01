# SocialGraph Contract

## Overview

Protocol for querying social graph relationships (follows). Enables in-network vs out-of-network classification for feed ranking.

## Protocol Definition

```python
from typing import Protocol

class SocialGraphProtocol(Protocol):
    """Protocol for social graph relationship queries."""

    def get_following(self, agent_id: str) -> set[str]:
        """Get the set of agent IDs that the given agent follows.

        Args:
            agent_id: The agent whose following list to retrieve.

        Returns:
            Set of agent IDs that this agent follows.
            Empty set if agent follows no one or agent not found.
        """
        ...

    def is_following(self, follower_id: str, followee_id: str) -> bool:
        """Check if follower follows followee.

        Args:
            follower_id: The agent who might be following.
            followee_id: The agent who might be followed.

        Returns:
            True if follower follows followee, False otherwise.
        """
        ...

    def get_followers(self, agent_id: str) -> set[str]:
        """Get the set of agent IDs that follow the given agent.

        Args:
            agent_id: The agent whose followers to retrieve.

        Returns:
            Set of agent IDs that follow this agent.
            Empty set if no followers or agent not found.
        """
        ...
```

## Simple Implementation

For MVP, the social graph is derived from `SocialAgent.following` fields:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from prism.agents.social_agent import SocialAgent

class SimpleSocialGraph:
    """Simple social graph backed by agent following sets."""

    def __init__(self, agents: list["SocialAgent"]) -> None:
        """Build graph from agent following sets.

        Args:
            agents: List of agents with .agent_id and .following fields.
        """
        self._following: dict[str, set[str]] = {
            agent.agent_id: agent.following
            for agent in agents
        }
        # Build reverse index for get_followers
        self._followers: dict[str, set[str]] = {}
        for agent_id, following in self._following.items():
            for followee_id in following:
                if followee_id not in self._followers:
                    self._followers[followee_id] = set()
                self._followers[followee_id].add(agent_id)

    def get_following(self, agent_id: str) -> set[str]:
        return self._following.get(agent_id, set())

    def is_following(self, follower_id: str, followee_id: str) -> bool:
        return followee_id in self._following.get(follower_id, set())

    def get_followers(self, agent_id: str) -> set[str]:
        return self._followers.get(agent_id, set())
```

## Integration with SimulationState

```python
class SimulationState(BaseModel):
    # ... existing fields ...

    def get_social_graph(self) -> SimpleSocialGraph:
        """Build social graph from current agents.

        Note: Rebuilds on each call. Cache if needed.
        """
        return SimpleSocialGraph(self.agents)
```

## Usage in Ranker

```python
class XAlgorithmRanker:
    def get_feed(
        self,
        agent: SocialAgent,
        social_graph: SocialGraphProtocol,
    ) -> list[Post]:
        following = social_graph.get_following(agent.agent_id)
        # Use following for INN/OON classification
```

## Future Extensions

- Edge weights (relationship strength from Real Graph)
- Mutual follows detection
- Community membership
- Follow/unfollow history
