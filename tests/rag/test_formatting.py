"""Tests for feed formatting functions."""

from datetime import datetime, timedelta

from prism.rag.models import Post


class TestFormatRelativeTime:
    """Test suite for format_relative_time() helper function."""

    def test_seconds_ago(self):
        """Recent timestamps show 'just now'."""
        from prism.rag.formatting import format_relative_time

        now = datetime.now()
        timestamp = now - timedelta(seconds=30)

        result = format_relative_time(timestamp, now)

        assert result == "just now"

    def test_minutes_ago(self):
        """Minutes ago formatted correctly."""
        from prism.rag.formatting import format_relative_time

        now = datetime.now()
        timestamp = now - timedelta(minutes=5)

        result = format_relative_time(timestamp, now)

        assert result == "5m ago"

    def test_one_minute_ago(self):
        """One minute ago formatted correctly."""
        from prism.rag.formatting import format_relative_time

        now = datetime.now()
        timestamp = now - timedelta(minutes=1)

        result = format_relative_time(timestamp, now)

        assert result == "1m ago"

    def test_hours_ago(self):
        """Hours ago formatted correctly."""
        from prism.rag.formatting import format_relative_time

        now = datetime.now()
        timestamp = now - timedelta(hours=3)

        result = format_relative_time(timestamp, now)

        assert result == "3h ago"

    def test_one_hour_ago(self):
        """One hour ago formatted correctly."""
        from prism.rag.formatting import format_relative_time

        now = datetime.now()
        timestamp = now - timedelta(hours=1)

        result = format_relative_time(timestamp, now)

        assert result == "1h ago"

    def test_days_ago(self):
        """Days ago formatted correctly."""
        from prism.rag.formatting import format_relative_time

        now = datetime.now()
        timestamp = now - timedelta(days=2)

        result = format_relative_time(timestamp, now)

        assert result == "2d ago"

    def test_one_day_ago(self):
        """One day ago formatted correctly."""
        from prism.rag.formatting import format_relative_time

        now = datetime.now()
        timestamp = now - timedelta(days=1)

        result = format_relative_time(timestamp, now)

        assert result == "1d ago"

    def test_weeks_ago(self):
        """Weeks ago formatted correctly."""
        from prism.rag.formatting import format_relative_time

        now = datetime.now()
        timestamp = now - timedelta(weeks=2)

        result = format_relative_time(timestamp, now)

        assert result == "2w ago"

    def test_boundary_59_minutes(self):
        """59 minutes shows minutes, not hours."""
        from prism.rag.formatting import format_relative_time

        now = datetime.now()
        timestamp = now - timedelta(minutes=59)

        result = format_relative_time(timestamp, now)

        assert result == "59m ago"

    def test_boundary_23_hours(self):
        """23 hours shows hours, not days."""
        from prism.rag.formatting import format_relative_time

        now = datetime.now()
        timestamp = now - timedelta(hours=23)

        result = format_relative_time(timestamp, now)

        assert result == "23h ago"


class TestFormatFeedForPrompt:
    """Test suite for format_feed_for_prompt() function."""

    def test_returns_string(self):
        """format_feed_for_prompt returns a string."""
        from prism.rag.formatting import format_feed_for_prompt

        posts = [
            Post(
                id="post_001",
                author_id="agent_1",
                text="Hello world",
                timestamp=datetime.now(),
            )
        ]

        result = format_feed_for_prompt(posts)

        assert isinstance(result, str)

    def test_includes_post_text(self):
        """Formatted output includes the post text."""
        from prism.rag.formatting import format_feed_for_prompt

        posts = [
            Post(
                id="post_001",
                author_id="agent_1",
                text="My local coffee shop now accepts Bitcoin!",
                timestamp=datetime.now(),
            )
        ]

        result = format_feed_for_prompt(posts)

        assert "My local coffee shop now accepts Bitcoin!" in result

    def test_includes_post_number(self):
        """Formatted output includes post numbering."""
        from prism.rag.formatting import format_feed_for_prompt

        posts = [
            Post(
                id="post_001",
                author_id="agent_1",
                text="First post",
                timestamp=datetime.now(),
            ),
            Post(
                id="post_002",
                author_id="agent_2",
                text="Second post",
                timestamp=datetime.now(),
            ),
        ]

        result = format_feed_for_prompt(posts)

        assert "Post #1:" in result
        assert "Post #2:" in result

    def test_includes_media_indicator_for_image(self):
        """Media indicator shown when has_media=True with image type."""
        from prism.rag.formatting import format_feed_for_prompt

        posts = [
            Post(
                id="post_001",
                author_id="agent_1",
                text="Check this out",
                timestamp=datetime.now(),
                has_media=True,
                media_type="image",
                media_description="A photo of sunset",
            )
        ]

        result = format_feed_for_prompt(posts)

        assert "[" in result and "IMAGE:" in result
        assert "A photo of sunset" in result

    def test_correct_emoji_for_image(self):
        """Image media type uses camera emoji."""
        from prism.rag.formatting import format_feed_for_prompt

        posts = [
            Post(
                id="post_001",
                author_id="agent_1",
                text="Photo post",
                timestamp=datetime.now(),
                has_media=True,
                media_type="image",
                media_description="Test image",
            )
        ]

        result = format_feed_for_prompt(posts)

        assert "IMAGE:" in result

    def test_correct_emoji_for_video(self):
        """Video media type uses movie camera emoji."""
        from prism.rag.formatting import format_feed_for_prompt

        posts = [
            Post(
                id="post_001",
                author_id="agent_1",
                text="Video post",
                timestamp=datetime.now(),
                has_media=True,
                media_type="video",
                media_description="Test video",
            )
        ]

        result = format_feed_for_prompt(posts)

        assert "VIDEO:" in result

    def test_correct_emoji_for_gif(self):
        """GIF media type uses film frames emoji."""
        from prism.rag.formatting import format_feed_for_prompt

        posts = [
            Post(
                id="post_001",
                author_id="agent_1",
                text="GIF post",
                timestamp=datetime.now(),
                has_media=True,
                media_type="gif",
                media_description="Funny animation",
            )
        ]

        result = format_feed_for_prompt(posts)

        assert "GIF:" in result

    def test_no_media_indicator_when_no_media(self):
        """No media indicator when has_media=False."""
        from prism.rag.formatting import format_feed_for_prompt

        posts = [
            Post(
                id="post_001",
                author_id="agent_1",
                text="Text only post",
                timestamp=datetime.now(),
                has_media=False,
            )
        ]

        result = format_feed_for_prompt(posts)

        assert "IMAGE:" not in result
        assert "VIDEO:" not in result
        assert "GIF:" not in result

    def test_includes_like_count(self):
        """Formatted output includes like count with heart emoji."""
        from prism.rag.formatting import format_feed_for_prompt

        posts = [
            Post(
                id="post_001",
                author_id="agent_1",
                text="Popular post",
                timestamp=datetime.now(),
                likes=89,
            )
        ]

        result = format_feed_for_prompt(posts)

        assert "89" in result

    def test_includes_reshare_count(self):
        """Formatted output includes reshare count."""
        from prism.rag.formatting import format_feed_for_prompt

        posts = [
            Post(
                id="post_001",
                author_id="agent_1",
                text="Viral post",
                timestamp=datetime.now(),
                reshares=34,
            )
        ]

        result = format_feed_for_prompt(posts)

        assert "34" in result

    def test_includes_reply_count(self):
        """Formatted output includes reply count."""
        from prism.rag.formatting import format_feed_for_prompt

        posts = [
            Post(
                id="post_001",
                author_id="agent_1",
                text="Discussion post",
                timestamp=datetime.now(),
                replies=12,
            )
        ]

        result = format_feed_for_prompt(posts)

        assert "12" in result

    def test_includes_relative_timestamp(self):
        """Formatted output includes relative timestamp."""
        from prism.rag.formatting import format_feed_for_prompt

        posts = [
            Post(
                id="post_001",
                author_id="agent_1",
                text="Recent post",
                timestamp=datetime.now() - timedelta(hours=3),
            )
        ]

        result = format_feed_for_prompt(posts)

        assert "3h ago" in result

    def test_empty_list_returns_empty_string(self):
        """Empty post list returns empty string."""
        from prism.rag.formatting import format_feed_for_prompt

        result = format_feed_for_prompt([])

        assert result == ""

    def test_multiple_posts_separated(self):
        """Multiple posts are visually separated."""
        from prism.rag.formatting import format_feed_for_prompt

        posts = [
            Post(
                id="post_001",
                author_id="agent_1",
                text="First post",
                timestamp=datetime.now(),
            ),
            Post(
                id="post_002",
                author_id="agent_2",
                text="Second post",
                timestamp=datetime.now(),
            ),
        ]

        result = format_feed_for_prompt(posts)

        # Should have both posts
        assert "First post" in result
        assert "Second post" in result
        # Posts should be separated (newlines between them)
        assert result.count("Post #") == 2

    def test_full_formatted_post(self):
        """Full post with all elements formats correctly."""
        from prism.rag.formatting import format_feed_for_prompt

        posts = [
            Post(
                id="post_001",
                author_id="agent_42",
                text="Just mass adoption? My local coffee shop accepts Bitcoin!",
                timestamp=datetime.now() - timedelta(hours=3),
                has_media=True,
                media_type="image",
                media_description="Photo of coffee shop with Bitcoin payment terminal",
                likes=89,
                reshares=34,
                replies=12,
            )
        ]

        result = format_feed_for_prompt(posts)

        # Check all elements are present
        assert "Post #1:" in result
        assert "Just mass adoption?" in result
        assert "IMAGE:" in result
        assert "Bitcoin payment terminal" in result
        assert "89" in result
        assert "34" in result
        assert "12" in result
        assert "3h ago" in result
