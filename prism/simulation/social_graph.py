"""Simple social graph implementation for X algorithm ranking.

This module provides a basic social graph backed by agent following sets,
implementing the SocialGraphProtocol for use with the XAlgorithmRanker.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from prism.agents.social_agent import SocialAgent


class SimpleSocialGraph:
    """Simple social graph backed by agent following sets.

    Builds a graph from agent.following attributes and provides efficient
    lookup for follow relationships needed by the ranking algorithm.
    """

    def __init__(self, agents: list["SocialAgent"]) -> None:
        """Build graph from agent following sets.

        Args:
            agents: List of agents with .agent_id and .following fields.
        """
        self._following: dict[str, set[str]] = {
            agent.agent_id: agent.following for agent in agents
        }

        # Build reverse index for get_followers
        self._followers: dict[str, set[str]] = {}
        for agent_id, following in self._following.items():
            for followee_id in following:
                if followee_id not in self._followers:
                    self._followers[followee_id] = set()
                self._followers[followee_id].add(agent_id)

    def get_following(self, agent_id: str) -> set[str]:
        """Get the set of agent IDs that the given agent follows.

        Args:
            agent_id: The agent whose following list to retrieve.

        Returns:
            Set of agent IDs that this agent follows.
            Empty set if agent follows no one or agent not found.
        """
        return self._following.get(agent_id, set())

    def is_following(self, follower_id: str, followee_id: str) -> bool:
        """Check if follower follows followee.

        Args:
            follower_id: The agent who might be following.
            followee_id: The agent who might be followed.

        Returns:
            True if follower follows followee, False otherwise.
        """
        return followee_id in self._following.get(follower_id, set())

    def get_followers(self, agent_id: str) -> set[str]:
        """Get the set of agent IDs that follow the given agent.

        Args:
            agent_id: The agent whose followers to retrieve.

        Returns:
            Set of agent IDs that follow this agent.
            Empty set if no followers or agent not found.
        """
        return self._followers.get(agent_id, set())
