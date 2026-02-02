"""Tests for SocialGraphProtocol and SimpleSocialGraph."""

from unittest.mock import MagicMock


def _create_mock_agent(agent_id: str, following: set[str] | None = None) -> MagicMock:
    """Create a mock agent with agent_id and following attributes."""
    agent = MagicMock()
    agent.agent_id = agent_id
    agent.following = following if following is not None else set()
    return agent


class TestSocialGraphProtocol:
    """Tests for SocialGraphProtocol interface definition."""

    def test_protocol_is_importable(self) -> None:
        """T029: SocialGraphProtocol should be importable from protocols module."""
        from prism.simulation.protocols import SocialGraphProtocol

        # Verify it's a Protocol (has required methods in __protocol_attrs__)
        assert hasattr(SocialGraphProtocol, "__protocol_attrs__") or hasattr(
            SocialGraphProtocol, "_is_protocol"
        )

    def test_protocol_has_get_following_method(self) -> None:
        """T029: Protocol should define get_following method."""
        import inspect

        from prism.simulation.protocols import SocialGraphProtocol

        # Get the method from the protocol
        assert hasattr(SocialGraphProtocol, "get_following")
        method = getattr(SocialGraphProtocol, "get_following")

        # Check signature: agent_id: str -> set[str]
        sig = inspect.signature(method)
        params = list(sig.parameters.keys())
        assert "agent_id" in params

    def test_protocol_has_is_following_method(self) -> None:
        """T029: Protocol should define is_following method."""
        import inspect

        from prism.simulation.protocols import SocialGraphProtocol

        assert hasattr(SocialGraphProtocol, "is_following")
        method = getattr(SocialGraphProtocol, "is_following")

        sig = inspect.signature(method)
        params = list(sig.parameters.keys())
        assert "follower_id" in params
        assert "followee_id" in params

    def test_protocol_has_get_followers_method(self) -> None:
        """T029: Protocol should define get_followers method."""
        import inspect

        from prism.simulation.protocols import SocialGraphProtocol

        assert hasattr(SocialGraphProtocol, "get_followers")
        method = getattr(SocialGraphProtocol, "get_followers")

        sig = inspect.signature(method)
        params = list(sig.parameters.keys())
        assert "agent_id" in params


class TestSimpleSocialGraph:
    """Tests for SimpleSocialGraph implementation."""

    def test_get_following_returns_correct_set(self) -> None:
        """T031: get_following should return the set of agents being followed."""
        from prism.simulation.social_graph import SimpleSocialGraph

        # Setup: agent1 follows agent2 and agent3
        agent1 = _create_mock_agent("agent1", following={"agent2", "agent3"})
        agent2 = _create_mock_agent("agent2", following={"agent1"})
        agent3 = _create_mock_agent("agent3", following=set())

        graph = SimpleSocialGraph([agent1, agent2, agent3])

        # Verify get_following returns correct sets
        assert graph.get_following("agent1") == {"agent2", "agent3"}
        assert graph.get_following("agent2") == {"agent1"}
        assert graph.get_following("agent3") == set()

    def test_is_following_returns_correct_bool(self) -> None:
        """T033: is_following should return True if follower follows followee."""
        from prism.simulation.social_graph import SimpleSocialGraph

        # Setup: agent1 follows agent2, agent2 does not follow agent1
        agent1 = _create_mock_agent("agent1", following={"agent2"})
        agent2 = _create_mock_agent("agent2", following=set())

        graph = SimpleSocialGraph([agent1, agent2])

        # Verify is_following returns correct booleans
        assert graph.is_following("agent1", "agent2") is True
        assert graph.is_following("agent2", "agent1") is False
        assert graph.is_following("agent1", "agent1") is False  # Self-follow check

    def test_get_followers_returns_reverse_lookup(self) -> None:
        """T035: get_followers should return agents who follow the given agent."""
        from prism.simulation.social_graph import SimpleSocialGraph

        # Setup: agent1 and agent2 both follow agent3
        agent1 = _create_mock_agent("agent1", following={"agent3"})
        agent2 = _create_mock_agent("agent2", following={"agent3"})
        agent3 = _create_mock_agent("agent3", following=set())

        graph = SimpleSocialGraph([agent1, agent2, agent3])

        # Verify get_followers returns the reverse relationship
        assert graph.get_followers("agent3") == {"agent1", "agent2"}
        assert graph.get_followers("agent1") == set()  # No one follows agent1
        assert graph.get_followers("agent2") == set()  # No one follows agent2

    def test_empty_following_set_returns_empty_set(self) -> None:
        """T037: Agent with no follows should return empty set."""
        from prism.simulation.social_graph import SimpleSocialGraph

        agent1 = _create_mock_agent("agent1", following=set())
        graph = SimpleSocialGraph([agent1])

        # Empty following set should return empty set
        assert graph.get_following("agent1") == set()
        assert graph.get_followers("agent1") == set()

    def test_missing_agent_returns_empty_set(self) -> None:
        """T037: Query for non-existent agent should return empty set."""
        from prism.simulation.social_graph import SimpleSocialGraph

        agent1 = _create_mock_agent("agent1", following={"agent2"})
        graph = SimpleSocialGraph([agent1])

        # Non-existent agent should return empty set (not raise error)
        assert graph.get_following("nonexistent") == set()
        assert graph.get_followers("nonexistent") == set()
        assert graph.is_following("nonexistent", "agent1") is False
        assert graph.is_following("agent1", "nonexistent") is False
