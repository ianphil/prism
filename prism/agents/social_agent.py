"""Social agent for making social media engagement decisions."""

import json
import logging
from datetime import datetime

from agent_framework.ollama import OllamaChatClient

from prism.agents.decision import AgentDecision
from prism.agents.prompts import build_feed_prompt, build_system_prompt
from prism.statechart.states import AgentState
from prism.statechart.transitions import StateTransition

logger = logging.getLogger(__name__)


class SocialAgent:
    """A social media agent that decides how to engage with feed content.

    The agent uses an LLM to make decisions about posts in a social media feed,
    choosing between LIKE, REPLY, RESHARE, or SCROLL based on their personality
    and interests.
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        interests: list[str],
        personality: str,
        client: OllamaChatClient,
        temperature: float = 0.7,
        max_tokens: int = 512,
        timeout_threshold: int = 5,
        max_history_depth: int = 100,
        engagement_threshold: float = 0.5,
    ) -> None:
        """Initialize a social agent.

        Args:
            agent_id: Unique identifier for this agent.
            name: Display name for the agent.
            interests: List of topics the agent cares about (must be non-empty).
            personality: Brief personality description.
            client: OllamaChatClient instance for LLM inference.
            temperature: Sampling temperature for LLM responses.
            max_tokens: Maximum tokens in LLM response.
            timeout_threshold: Ticks before agent is considered timed out (must be > 0).
            max_history_depth: Maximum number of state transitions to keep in history.
            engagement_threshold: Relevance threshold for should_engage() guard.

        Raises:
            ValueError: If interests list is empty or timeout_threshold <= 0.
        """
        if not interests:
            raise ValueError("interests must be a non-empty list")
        if timeout_threshold <= 0:
            raise ValueError("timeout_threshold must be > 0")

        self.agent_id = agent_id
        self.name = name
        self.interests = interests
        self.personality = personality
        self._client = client
        self._temperature = temperature
        self._max_tokens = max_tokens

        # Timeout tracking (Phase 4)
        self.timeout_threshold = timeout_threshold
        self.ticks_in_state: int = 0

        # State tracking (Phase 5)
        self.state: AgentState = AgentState.IDLE
        self.state_history: list[StateTransition] = []
        self.max_history_depth = max_history_depth
        self.engagement_threshold = engagement_threshold

        # Build the system prompt from profile
        self._system_prompt = build_system_prompt(
            name=name,
            interests=interests,
            personality=personality,
        )

        # Create the underlying ChatAgent
        self._agent = self._client.as_agent(
            name=agent_id,
            instructions=self._system_prompt,
        )

    async def decide(self, feed_text: str) -> AgentDecision:
        """Make a decision about how to engage with the given feed content.

        Args:
            feed_text: The content of the post/feed to evaluate.

        Returns:
            AgentDecision with the agent's choice, reason, and optional content.
        """
        user_prompt = build_feed_prompt(feed_text)

        try:
            response = await self._agent.run(
                user_prompt,
                options={
                    "temperature": self._temperature,
                    "max_tokens": self._max_tokens,
                    "response_format": "json",
                },
            )

            # Try structured output first (if supported)
            if response.value is not None:
                if isinstance(response.value, AgentDecision):
                    return response.value
                # If value is a dict, try to construct AgentDecision
                if isinstance(response.value, dict):
                    return AgentDecision(**response.value)

            # Fallback: parse JSON from text response
            return self._parse_response_text(response.text)

        except Exception as e:
            logger.warning(f"Agent {self.agent_id} decision failed: {e}")
            return self._default_scroll_decision(f"Decision error: {e}")

    def _parse_response_text(self, text: str) -> AgentDecision:
        """Parse response text as JSON into AgentDecision.

        Args:
            text: Raw text response from the LLM.

        Returns:
            AgentDecision parsed from the text.
        """
        try:
            # Try to parse as JSON
            data = json.loads(text)
            return AgentDecision(**data)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error for agent {self.agent_id}: {e}")
            return self._default_scroll_decision(f"JSON parse error: {e}")
        except Exception as e:
            logger.warning(f"Validation error for agent {self.agent_id}: {e}")
            return self._default_scroll_decision(f"Validation error: {e}")

    def _default_scroll_decision(self, reason: str) -> AgentDecision:
        """Create a default SCROLL decision for error cases.

        Args:
            reason: The reason for the fallback decision.

        Returns:
            AgentDecision with SCROLL choice.
        """
        return AgentDecision(
            choice="SCROLL",
            reason=reason,
            content=None,
        )

    def tick(self) -> None:
        """Increment ticks_in_state counter.

        Called once per simulation round for timeout detection.
        """
        self.ticks_in_state += 1

    def is_timed_out(self) -> bool:
        """Check if agent has been in current state too long.

        Returns:
            True if ticks_in_state > timeout_threshold.
        """
        return self.ticks_in_state > self.timeout_threshold

    def transition_to(
        self,
        new_state: AgentState,
        trigger: str,
        context: dict | None = None,
    ) -> None:
        """Transition agent to a new state.

        Records the transition in history and resets tick counter.
        No-op if new_state equals current state (self-transition).

        Args:
            new_state: The target AgentState to transition to.
            trigger: The event that caused this transition.
            context: Optional context dict (e.g., post_id, relevance).
        """
        # No-op for self-transitions
        if new_state == self.state:
            return

        # Record the transition
        transition = StateTransition(
            from_state=self.state,
            to_state=new_state,
            trigger=trigger,
            timestamp=datetime.now(),
            context=context,
        )
        self.state_history.append(transition)

        # Prune history if it exceeds max depth (FIFO - remove oldest first)
        if len(self.state_history) > self.max_history_depth:
            self.state_history = self.state_history[-self.max_history_depth:]

        # Update state and reset tick counter
        self.state = new_state
        self.ticks_in_state = 0

    def should_engage(self, relevance: float) -> bool:
        """Guard helper to determine if agent should engage with content.

        Used as a guard condition in statechart transitions.

        Args:
            relevance: A score from 0.0 to 1.0 indicating content relevance.

        Returns:
            True if relevance >= engagement_threshold.
        """
        return relevance >= self.engagement_threshold
