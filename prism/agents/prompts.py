"""Prompt building utilities for social agents."""

from prism.agents.profiles import AgentProfile
from prism.models.post import Post


def build_system_prompt(profile: AgentProfile) -> str:
    """Build the system prompt from an agent profile.

    The system prompt establishes the agent's identity, interests,
    personality, and decision-making constraints.

    Args:
        profile: Agent profile with identity and characteristics.

    Returns:
        System prompt string for the LLM.
    """
    interests = ", ".join(profile.interests)

    prompt = f"""You are {profile.name}, a social media user.

Your interests: {interests}
Your personality: {profile.personality}

When shown a feed of posts, you must decide how to engage with ONE post.

Your options are:
- IGNORE: Skip the post (not interesting or relevant)
- LIKE: Show appreciation (agree or find it interesting)
- REPLY: Write a response (want to engage in conversation)
- RESHARE: Share with your followers (valuable content worth amplifying)

You MUST respond in this exact JSON format:
{{
    "choice": "IGNORE" | "LIKE" | "REPLY" | "RESHARE",
    "reason": "Brief explanation of why you made this choice",
    "content": "Your reply/reshare comment (null for IGNORE/LIKE)",
    "post_id": "ID of the post you're responding to"
}}

Guidelines:
- Be authentic to your personality and interests
- Engage naturally, like a real person would
- For REPLY: Write conversational, engaging responses
- For RESHARE: Add your own perspective or comment
- Only engage with posts relevant to your interests
- You may IGNORE posts that don't interest you
"""

    # Add stance information if present
    if profile.stance:
        stance_lines = [
            f"- {topic}: {position}"
            for topic, position in profile.stance.items()
        ]
        stance_text = "\n".join(stance_lines)
        prompt += f"\nYour positions on topics:\n{stance_text}\n"

    return prompt


def build_user_prompt(feed: list[Post], profile: AgentProfile) -> str:
    """Build the user prompt from a feed of posts.

    Formats the feed posts for the agent to evaluate, including
    engagement stats and media indicators.

    Args:
        feed: List of posts to present to the agent.
        profile: Agent profile (used for context).

    Returns:
        User prompt string with formatted feed.
    """
    if not feed:
        return "Your feed is empty. Respond with IGNORE and post_id of 'none'."

    lines = [
        f"Here is your feed, {profile.name}. Choose ONE post to engage with:\n"
    ]

    for i, post in enumerate(feed, 1):
        lines.append(f"--- Post #{i} (ID: {post.id}) ---")
        lines.append(post.format_for_prompt())
        lines.append("")

    lines.append("Respond with your decision in JSON format.")

    return "\n".join(lines)


def parse_decision_response(
    response: str,
    fallback_post_id: str | None = None,
) -> dict:
    """Parse the LLM response into a decision dictionary.

    Attempts to extract JSON from the response, with fallback
    handling for malformed responses.

    Args:
        response: Raw LLM response text.
        fallback_post_id: Post ID to use if not found in response.

    Returns:
        Dictionary with choice, reason, content, and post_id keys.

    Raises:
        ValueError: If response cannot be parsed into a valid decision.
    """
    import json
    import re

    # Try to extract JSON from the response
    # Look for JSON object pattern
    json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)

    if json_match:
        try:
            data = json.loads(json_match.group())

            # Validate required fields
            if "choice" not in data:
                raise ValueError("Response missing 'choice' field")

            # Normalize choice to uppercase
            data["choice"] = data["choice"].upper()

            # Ensure reason exists
            if "reason" not in data or not data["reason"]:
                data["reason"] = "No reason provided"

            # Handle content field
            if "content" not in data:
                data["content"] = None

            # Handle post_id
            if "post_id" not in data or not data["post_id"]:
                if fallback_post_id:
                    data["post_id"] = fallback_post_id
                else:
                    raise ValueError("Response missing 'post_id' field")

            return data

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in response: {e}") from e

    # If no JSON found, try to extract decision from text
    # This is a fallback for models that don't follow format perfectly
    response_upper = response.upper()

    for choice in ["RESHARE", "REPLY", "LIKE", "IGNORE"]:
        if choice in response_upper:
            return {
                "choice": choice,
                "reason": "Extracted from unstructured response",
                "content": response if choice in ["REPLY", "RESHARE"] else None,
                "post_id": fallback_post_id or "unknown",
            }

    raise ValueError(f"Could not parse decision from response: {response[:200]}")
