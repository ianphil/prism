"""Social agent for making social media engagement decisions."""

import json
import logging

from agent_framework.ollama import OllamaChatClient

from prism.agents.decision import AgentDecision
from prism.agents.prompts import build_feed_prompt, build_system_prompt

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
    ) -> None:
        """Initialize a social agent.

        Args:
            agent_id: Unique identifier for this agent.
            name: Display name for the agent.
            interests: List of topics the agent cares about.
            personality: Brief personality description.
            client: OllamaChatClient instance for LLM inference.
            temperature: Sampling temperature for LLM responses.
            max_tokens: Maximum tokens in LLM response.
        """
        self.agent_id = agent_id
        self.name = name
        self.interests = interests
        self.personality = personality
        self._client = client
        self._temperature = temperature
        self._max_tokens = max_tokens

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
