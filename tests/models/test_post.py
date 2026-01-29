"""Tests for post data model."""

from datetime import datetime, timedelta

import pytest

from prism.models.post import Post


class TestPost:
    """Tests for the Post dataclass."""

    def test_post_creation(self) -> None:
        """Post should be creatable with required fields."""
        post = Post(
            id="post_001",
            author_id="agent_001",
            text="Hello world!",
            timestamp=datetime.now(),
        )
        assert post.id == "post_001"
        assert post.author_id == "agent_001"
        assert post.text == "Hello world!"

    def test_post_default_values(self) -> None:
        """Post should have sensible defaults."""
        post = Post(
            id="post_001",
            author_id="agent_001",
            text="Test",
            timestamp=datetime.now(),
        )
        assert post.has_media is False
        assert post.media_type is None
        assert post.media_description is None
        assert post.likes == 0
        assert post.reshares == 0
        assert post.replies == 0
        assert post.velocity == 0.0

    def test_post_with_media(self) -> None:
        """Post should accept media fields."""
        post = Post(
            id="post_002",
            author_id="agent_001",
            text="Check out this photo!",
            timestamp=datetime.now(),
            has_media=True,
            media_type="image",
            media_description="A beautiful sunset over the ocean",
        )
        assert post.has_media is True
        assert post.media_type == "image"
        assert post.media_description == "A beautiful sunset over the ocean"

    def test_post_with_engagement(self) -> None:
        """Post should accept engagement metrics."""
        post = Post(
            id="post_003",
            author_id="agent_001",
            text="Popular post",
            timestamp=datetime.now(),
            likes=100,
            reshares=50,
            replies=25,
        )
        assert post.likes == 100
        assert post.reshares == 50
        assert post.replies == 25

    def test_engagement_count_property(self) -> None:
        """Engagement count should sum all metrics."""
        post = Post(
            id="post_003",
            author_id="agent_001",
            text="Test",
            timestamp=datetime.now(),
            likes=10,
            reshares=5,
            replies=3,
        )
        assert post.engagement_count == 18

    def test_has_media_requires_media_type(self) -> None:
        """has_media=True requires media_type."""
        with pytest.raises(ValueError, match="media_type is required"):
            Post(
                id="post_001",
                author_id="agent_001",
                text="Test",
                timestamp=datetime.now(),
                has_media=True,
            )

    def test_negative_likes_raises(self) -> None:
        """Negative likes should raise ValueError."""
        with pytest.raises(ValueError, match="likes must be >= 0"):
            Post(
                id="post_001",
                author_id="agent_001",
                text="Test",
                timestamp=datetime.now(),
                likes=-1,
            )

    def test_negative_reshares_raises(self) -> None:
        """Negative reshares should raise ValueError."""
        with pytest.raises(ValueError, match="reshares must be >= 0"):
            Post(
                id="post_001",
                author_id="agent_001",
                text="Test",
                timestamp=datetime.now(),
                reshares=-1,
            )

    def test_negative_replies_raises(self) -> None:
        """Negative replies should raise ValueError."""
        with pytest.raises(ValueError, match="replies must be >= 0"):
            Post(
                id="post_001",
                author_id="agent_001",
                text="Test",
                timestamp=datetime.now(),
                replies=-1,
            )


class TestPostFormatting:
    """Tests for post formatting methods."""

    def test_format_for_prompt_basic(self) -> None:
        """Basic post formatting for prompts."""
        post = Post(
            id="post_001",
            author_id="agent_001",
            text="Hello world!",
            timestamp=datetime.now() - timedelta(hours=2),
            likes=10,
            reshares=5,
            replies=2,
        )
        formatted = post.format_for_prompt()
        assert '"Hello world!"' in formatted
        assert "❤️ 10" in formatted
        assert "🔁 5" in formatted
        assert "💬 2" in formatted
        assert "2h ago" in formatted

    def test_format_for_prompt_with_image(self) -> None:
        """Post with image formatting for prompts."""
        post = Post(
            id="post_002",
            author_id="agent_001",
            text="Check this out!",
            timestamp=datetime.now() - timedelta(minutes=30),
            has_media=True,
            media_type="image",
            media_description="Bitcoin payment terminal",
        )
        formatted = post.format_for_prompt()
        assert "📷 IMAGE: Bitcoin payment terminal" in formatted

    def test_format_for_prompt_with_video(self) -> None:
        """Post with video formatting for prompts."""
        post = Post(
            id="post_003",
            author_id="agent_001",
            text="Watch this!",
            timestamp=datetime.now() - timedelta(days=1),
            has_media=True,
            media_type="video",
            media_description="Product demo",
        )
        formatted = post.format_for_prompt()
        assert "🎬 VIDEO: Product demo" in formatted
        assert "1d ago" in formatted

    def test_format_time_ago_minutes(self) -> None:
        """Time ago formatting for minutes."""
        post = Post(
            id="post_001",
            author_id="agent_001",
            text="Test",
            timestamp=datetime.now() - timedelta(minutes=15),
        )
        formatted = post.format_for_prompt()
        assert "15m ago" in formatted

    def test_format_time_ago_hours(self) -> None:
        """Time ago formatting for hours."""
        post = Post(
            id="post_001",
            author_id="agent_001",
            text="Test",
            timestamp=datetime.now() - timedelta(hours=5),
        )
        formatted = post.format_for_prompt()
        assert "5h ago" in formatted

    def test_format_time_ago_days(self) -> None:
        """Time ago formatting for days."""
        post = Post(
            id="post_001",
            author_id="agent_001",
            text="Test",
            timestamp=datetime.now() - timedelta(days=3),
        )
        formatted = post.format_for_prompt()
        assert "3d ago" in formatted
