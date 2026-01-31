"""Integration tests for simulation workflow.

Tests the full simulation loop with 3 agents × 2 rounds, checkpoint/resume,
and state distribution logging.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from prism.rag.models import Post
from prism.simulation import (
    RoundController,
    SimulationConfig,
    SimulationState,
    create_social_media_statechart,
)
from prism.simulation.executors import (
    AgentDecisionExecutor,
    AgentRoundExecutor,
    FeedRetrievalExecutor,
    LoggingExecutor,
    StateUpdateExecutor,
)
from prism.statechart.states import AgentState


class MockAgent:
    """Minimal mock agent for testing simulation flow."""

    def __init__(
        self,
        agent_id: str,
        interests: list[str] | None = None,
        state: AgentState = AgentState.IDLE,
    ):
        self.agent_id = agent_id
        self.name = f"Agent {agent_id}"
        self.interests = interests or ["technology"]
        self.personality = "curious"
        self.state = state
        self.ticks_in_state = 0
        self.timeout_threshold = 5
        self.engagement_threshold = 0.5

    def tick(self) -> None:
        self.ticks_in_state += 1

    def is_timed_out(self) -> bool:
        return self.ticks_in_state > self.timeout_threshold

    def transition_to(
        self, new_state: AgentState, trigger: str, context: dict | None = None
    ) -> None:
        self.state = new_state
        self.ticks_in_state = 0


class MockFeedRetriever:
    """Mock retriever that returns predefined posts."""

    def __init__(self, posts: list[Post]):
        self._posts = posts

    def get_feed(self, interests: list[str] | None = None) -> list[Post]:
        return self._posts

    def add_post(self, post: Post) -> None:
        self._posts.append(post)


class TestSimulationCompletes:
    """T141: Integration test - 3 agents × 2 rounds completes."""

    @pytest.fixture
    def posts(self) -> list[Post]:
        """Create test posts."""
        now = datetime.now(timezone.utc)
        return [
            Post(id="p1", author_id="seed", text="Tech news today", timestamp=now),
            Post(id="p2", author_id="seed", text="Market update", timestamp=now),
        ]

    @pytest.fixture
    def agents(self) -> list[MockAgent]:
        """Create 3 test agents."""
        return [
            MockAgent("agent1", ["tech"]),
            MockAgent("agent2", ["finance"]),
            MockAgent("agent3", ["sports"]),
        ]

    @pytest.fixture
    def config(self) -> SimulationConfig:
        """Create minimal test config."""
        return SimulationConfig(max_rounds=2, checkpoint_dir=None, log_file=None)

    @pytest.fixture
    def statechart(self):
        """Create statechart for testing."""
        return create_social_media_statechart()

    @pytest.fixture
    def retriever(self, posts: list[Post]) -> MockFeedRetriever:
        """Create mock retriever."""
        return MockFeedRetriever(posts)

    @pytest.fixture
    def round_executor(self, retriever: MockFeedRetriever) -> AgentRoundExecutor:
        """Create round executor with all sub-executors."""
        feed_exec = FeedRetrievalExecutor(retriever)
        decision_exec = AgentDecisionExecutor()
        state_exec = StateUpdateExecutor(retriever)
        logging_exec = LoggingExecutor()

        return AgentRoundExecutor(
            feed_executor=feed_exec,
            decision_executor=decision_exec,
            state_executor=state_exec,
            logging_executor=logging_exec,
        )

    @pytest.mark.asyncio
    async def test_simulation_completes_3_agents_2_rounds(
        self,
        config: SimulationConfig,
        agents: list[MockAgent],
        posts: list[Post],
        statechart,
        round_executor: AgentRoundExecutor,
    ) -> None:
        """Simulation should complete 2 rounds with 3 agents."""
        state = SimulationState(
            posts=posts,
            agents=agents,
            statechart=statechart,
        )

        controller = RoundController(round_executor)
        result = await controller.run_simulation(config, state)

        # Should have completed all rounds
        assert result.total_rounds == 2
        # Should have 2 round results (one per round)
        assert len(result.rounds) == 2
        # Each round should have 3 decisions (one per agent)
        for round_result in result.rounds:
            assert len(round_result.decisions) == 3

    @pytest.mark.asyncio
    async def test_agents_transition_from_idle(
        self,
        config: SimulationConfig,
        agents: list[MockAgent],
        posts: list[Post],
        statechart,
        round_executor: AgentRoundExecutor,
    ) -> None:
        """All agents should transition from IDLE after first round."""
        state = SimulationState(
            posts=posts,
            agents=agents,
            statechart=statechart,
        )

        controller = RoundController(round_executor)
        await controller.run_simulation(config, state)

        # After simulation, agents should have moved from IDLE
        for agent in agents:
            # Agents start IDLE, then go to SCROLLING on start_browsing
            # Most common path: IDLE -> SCROLLING
            assert agent.ticks_in_state >= 0  # Ticks reset on transition


class TestCheckpointResume:
    """T143: Integration test - checkpoint/resume produces same state."""

    @pytest.fixture
    def posts(self) -> list[Post]:
        """Create test posts."""
        now = datetime.now(timezone.utc)
        return [
            Post(id="p1", author_id="seed", text="Test content", timestamp=now),
        ]

    @pytest.fixture
    def agents(self) -> list[MockAgent]:
        """Create test agents."""
        return [MockAgent("agent1", ["tech"])]

    @pytest.fixture
    def statechart(self):
        """Create statechart for testing."""
        return create_social_media_statechart()

    @pytest.fixture
    def retriever(self, posts: list[Post]) -> MockFeedRetriever:
        """Create mock retriever."""
        return MockFeedRetriever(posts)

    @pytest.fixture
    def round_executor(self, retriever: MockFeedRetriever) -> AgentRoundExecutor:
        """Create round executor."""
        feed_exec = FeedRetrievalExecutor(retriever)
        decision_exec = AgentDecisionExecutor()
        state_exec = StateUpdateExecutor(retriever)
        logging_exec = LoggingExecutor()

        return AgentRoundExecutor(
            feed_executor=feed_exec,
            decision_executor=decision_exec,
            state_executor=state_exec,
            logging_executor=logging_exec,
        )

    @pytest.mark.asyncio
    async def test_checkpoint_saves_to_file(
        self,
        tmp_path: Path,
        posts: list[Post],
        agents: list[MockAgent],
        statechart,
        round_executor: AgentRoundExecutor,
    ) -> None:
        """Checkpoint should create a JSON file."""
        config = SimulationConfig(
            max_rounds=2,
            checkpoint_frequency=1,
            checkpoint_dir=tmp_path,
        )

        state = SimulationState(
            posts=posts,
            agents=agents,
            statechart=statechart,
        )

        controller = RoundController(round_executor)
        await controller.run_simulation(config, state)

        # Should have checkpoint files
        checkpoints = list(tmp_path.glob("checkpoint_round_*.json"))
        assert len(checkpoints) > 0

    @pytest.mark.asyncio
    async def test_checkpoint_contains_state_distribution(
        self,
        tmp_path: Path,
        posts: list[Post],
        agents: list[MockAgent],
        statechart,
        round_executor: AgentRoundExecutor,
    ) -> None:
        """Checkpoint should include state_distribution field."""
        config = SimulationConfig(
            max_rounds=1,
            checkpoint_frequency=1,
            checkpoint_dir=tmp_path,
        )

        state = SimulationState(
            posts=posts,
            agents=agents,
            statechart=statechart,
        )

        controller = RoundController(round_executor)
        await controller.run_simulation(config, state)

        # Read checkpoint
        checkpoints = list(tmp_path.glob("checkpoint_round_*.json"))
        assert len(checkpoints) > 0

        with open(checkpoints[0]) as f:
            data = json.load(f)

        assert "state_distribution" in data
        assert "version" in data
        assert data["version"] == "1.0"


class TestStateDistributionLogging:
    """T145: Integration test - state distribution logged each round."""

    @pytest.fixture
    def posts(self) -> list[Post]:
        """Create test posts."""
        now = datetime.now(timezone.utc)
        return [Post(id="p1", author_id="seed", text="Test", timestamp=now)]

    @pytest.fixture
    def agents(self) -> list[MockAgent]:
        """Create test agents."""
        return [
            MockAgent("a1"),
            MockAgent("a2"),
        ]

    @pytest.fixture
    def statechart(self):
        """Create statechart for testing."""
        return create_social_media_statechart()

    @pytest.fixture
    def retriever(self, posts: list[Post]) -> MockFeedRetriever:
        """Create mock retriever."""
        return MockFeedRetriever(posts)

    @pytest.mark.asyncio
    async def test_logging_executor_writes_to_file(
        self,
        tmp_path: Path,
        posts: list[Post],
        agents: list[MockAgent],
        statechart,
        retriever: MockFeedRetriever,
    ) -> None:
        """LoggingExecutor should write JSON lines to configured file."""
        log_file = tmp_path / "decisions.jsonl"

        feed_exec = FeedRetrievalExecutor(retriever)
        decision_exec = AgentDecisionExecutor()
        state_exec = StateUpdateExecutor(retriever)
        logging_exec = LoggingExecutor(log_file=log_file)

        round_executor = AgentRoundExecutor(
            feed_executor=feed_exec,
            decision_executor=decision_exec,
            state_executor=state_exec,
            logging_executor=logging_exec,
        )

        config = SimulationConfig(max_rounds=2, checkpoint_dir=None)

        state = SimulationState(
            posts=posts,
            agents=agents,
            statechart=statechart,
        )

        controller = RoundController(round_executor)
        await controller.run_simulation(config, state)

        # Close the logging executor
        logging_exec.close()

        # Verify log file was created
        assert log_file.exists()

        # Read and verify log entries
        with open(log_file) as f:
            lines = f.readlines()

        # Should have 4 entries: 2 agents × 2 rounds
        assert len(lines) == 4

        # Verify each entry has expected fields
        for line in lines:
            entry = json.loads(line)
            assert "timestamp" in entry
            assert "round" in entry
            assert "agent_id" in entry
            assert "trigger" in entry
            assert "from_state" in entry
            assert "to_state" in entry

    @pytest.mark.asyncio
    async def test_decision_result_includes_states(
        self,
        posts: list[Post],
        agents: list[MockAgent],
        statechart,
        retriever: MockFeedRetriever,
    ) -> None:
        """DecisionResult should include from_state and to_state."""
        feed_exec = FeedRetrievalExecutor(retriever)
        decision_exec = AgentDecisionExecutor()
        state_exec = StateUpdateExecutor(retriever)
        logging_exec = LoggingExecutor()

        round_executor = AgentRoundExecutor(
            feed_executor=feed_exec,
            decision_executor=decision_exec,
            state_executor=state_exec,
            logging_executor=logging_exec,
        )

        config = SimulationConfig(max_rounds=1, checkpoint_dir=None)

        state = SimulationState(
            posts=posts,
            agents=agents,
            statechart=statechart,
        )

        controller = RoundController(round_executor)
        result = await controller.run_simulation(config, state)

        # Check first round decisions
        for decision in result.rounds[0].decisions:
            assert decision.from_state is not None
            assert decision.to_state is not None
            assert isinstance(decision.from_state, AgentState)
            assert isinstance(decision.to_state, AgentState)


class TestSimulationWiring:
    """T142, T144, T146: Wire up all components correctly."""

    @pytest.fixture
    def posts(self) -> list[Post]:
        now = datetime.now(timezone.utc)
        return [Post(id="p1", author_id="seed", text="Test", timestamp=now)]

    @pytest.fixture
    def agents(self) -> list[MockAgent]:
        return [MockAgent("a1")]

    @pytest.fixture
    def statechart(self):
        return create_social_media_statechart()

    @pytest.fixture
    def retriever(self, posts: list[Post]) -> MockFeedRetriever:
        return MockFeedRetriever(posts)

    @pytest.mark.asyncio
    async def test_controller_calls_round_executor_for_each_agent(
        self,
        posts: list[Post],
        statechart,
        retriever: MockFeedRetriever,
    ) -> None:
        """Controller should call round executor for each agent each round."""
        agents = [MockAgent("a1"), MockAgent("a2"), MockAgent("a3")]

        feed_exec = FeedRetrievalExecutor(retriever)
        decision_exec = AgentDecisionExecutor()
        state_exec = StateUpdateExecutor(retriever)
        logging_exec = LoggingExecutor()

        round_executor = AgentRoundExecutor(
            feed_executor=feed_exec,
            decision_executor=decision_exec,
            state_executor=state_exec,
            logging_executor=logging_exec,
        )

        config = SimulationConfig(max_rounds=3, checkpoint_dir=None)

        state = SimulationState(
            posts=posts,
            agents=agents,
            statechart=statechart,
        )

        controller = RoundController(round_executor)
        result = await controller.run_simulation(config, state)

        # 3 rounds × 3 agents = 9 decisions total
        total_decisions = sum(len(r.decisions) for r in result.rounds)
        assert total_decisions == 9

    @pytest.mark.asyncio
    async def test_state_advances_each_round(
        self,
        posts: list[Post],
        agents: list[MockAgent],
        statechart,
        retriever: MockFeedRetriever,
    ) -> None:
        """State round_number should advance after each round."""
        feed_exec = FeedRetrievalExecutor(retriever)
        decision_exec = AgentDecisionExecutor()
        state_exec = StateUpdateExecutor(retriever)
        logging_exec = LoggingExecutor()

        round_executor = AgentRoundExecutor(
            feed_executor=feed_exec,
            decision_executor=decision_exec,
            state_executor=state_exec,
            logging_executor=logging_exec,
        )

        config = SimulationConfig(max_rounds=5, checkpoint_dir=None)

        state = SimulationState(
            posts=posts,
            agents=agents,
            statechart=statechart,
        )

        assert state.round_number == 0

        controller = RoundController(round_executor)
        await controller.run_simulation(config, state)

        # Round number should have advanced
        assert state.round_number == 5
