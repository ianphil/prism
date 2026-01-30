"""Feed formatting functions for agent prompts."""

from datetime import datetime

from prism.rag.models import Post

# Media type to emoji mapping
MEDIA_EMOJI: dict[str, str] = {
    "image": "IMAGE:",
    "video": "VIDEO:",
    "gif": "GIF:",
}


def format_relative_time(timestamp: datetime, now: datetime | None = None) -> str:
    """Format a timestamp as relative time (e.g., "3h ago").

    Args:
        timestamp: The timestamp to format.
        now: Reference time for "now". Defaults to datetime.now().

    Returns:
        Relative time string like "5m ago", "3h ago", "2d ago".
    """
    if now is None:
        now = datetime.now()

    delta = now - timestamp
    total_seconds = int(delta.total_seconds())

    if total_seconds < 60:
        return "just now"

    minutes = total_seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"

    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"

    days = hours // 24
    if days < 7:
        return f"{days}d ago"

    weeks = days // 7
    return f"{weeks}w ago"


def format_feed_for_prompt(
    posts: list[Post],
    now: datetime | None = None,
) -> str:
    """Format a list of posts for agent prompt consumption.

    Renders posts with:
    - Post numbering
    - Post text
    - Media indicators with emoji (if has_media)
    - Engagement stats (likes, reshares, replies)
    - Relative timestamp

    Args:
        posts: List of Post objects to format.
        now: Reference time for relative timestamps. Defaults to datetime.now().

    Returns:
        Formatted string suitable for agent prompts.

    Example output:
        Post #1:
        "Just mass adoption starting? My local coffee shop now accepts Bitcoin!"
        [IMAGE: Photo of a coffee shop counter with a Bitcoin payment terminal]
        89 | 34 | 12 | 3h ago
    """
    if not posts:
        return ""

    if now is None:
        now = datetime.now()

    formatted_posts: list[str] = []

    for i, post in enumerate(posts, start=1):
        lines: list[str] = []

        # Post header with number
        lines.append(f"Post #{i}:")

        # Post text (quoted)
        lines.append(f'"{post.text}"')

        # Media indicator (if applicable)
        if post.has_media and post.media_type:
            emoji_label = MEDIA_EMOJI.get(post.media_type, "MEDIA:")
            description = post.media_description or "No description"
            lines.append(f"[{emoji_label} {description}]")

        # Engagement stats and timestamp
        relative_time = format_relative_time(post.timestamp, now)
        stats = f"{post.likes} | {post.reshares} | {post.replies} | {relative_time}"
        lines.append(stats)

        formatted_posts.append("\n".join(lines))

    return "\n\n".join(formatted_posts)
