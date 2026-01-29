"""Post data model."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Post:
    """A social media post that agents evaluate.

    Attributes:
        id: Unique post identifier.
        author_id: ID of the posting agent.
        text: Post content.
        timestamp: When posted.
        has_media: Whether post has visual content.
        media_type: Type of media ("image", "video", "gif").
        media_description: Description of visual content.
        likes: Current like count.
        reshares: Current reshare count.
        replies: Current reply count.
        velocity: Engagement rate over time (for ranking).
    """

    id: str
    author_id: str
    text: str
    timestamp: datetime
    has_media: bool = False
    media_type: str | None = None
    media_description: str | None = None
    likes: int = 0
    reshares: int = 0
    replies: int = 0
    velocity: float = 0.0

    def __post_init__(self) -> None:
        """Validate post fields."""
        if self.has_media and self.media_type is None:
            raise ValueError("media_type is required when has_media is True")
        if self.likes < 0:
            raise ValueError("likes must be >= 0")
        if self.reshares < 0:
            raise ValueError("reshares must be >= 0")
        if self.replies < 0:
            raise ValueError("replies must be >= 0")

    @property
    def engagement_count(self) -> int:
        """Total engagement (likes + reshares + replies)."""
        return self.likes + self.reshares + self.replies

    def format_for_prompt(self) -> str:
        """Format post for inclusion in agent prompt."""
        lines = [f'"{self.text}"']

        if self.has_media and self.media_description:
            emoji = {"image": "📷", "video": "🎬", "gif": "🎞️"}.get(
                self.media_type, "📎"
            )
            mtype = self.media_type.upper()
            lines.append(f"[{emoji} {mtype}: {self.media_description}]")

        # Engagement stats
        time_ago = self._format_time_ago()
        stats = f"❤️ {self.likes} | 🔁 {self.reshares} | 💬 {self.replies} | {time_ago}"
        lines.append(stats)

        return "\n".join(lines)

    def _format_time_ago(self) -> str:
        """Format timestamp as relative time."""
        delta = datetime.now() - self.timestamp
        hours = delta.total_seconds() / 3600

        if hours < 1:
            minutes = int(delta.total_seconds() / 60)
            return f"{minutes}m ago"
        elif hours < 24:
            return f"{int(hours)}h ago"
        else:
            days = int(hours / 24)
            return f"{days}d ago"
