"""Integration tests for the RAG feed system."""

from datetime import datetime, timedelta

import pytest

from prism.rag import (
    FeedRetriever,
    Post,
    RAGConfig,
    create_collection,
    format_feed_for_prompt,
)


@pytest.fixture
def sample_posts() -> list[Post]:
    """Create sample posts for testing."""
    now = datetime.now()
    return [
        Post(
            id="post_001",
            author_id="agent_crypto",
            text="Bitcoin just hit a new all-time high! The future of finance is here.",
            timestamp=now - timedelta(hours=2),
            has_media=True,
            media_type="image",
            media_description="Bitcoin price chart showing upward trend",
            likes=150,
            reshares=45,
            replies=23,
            velocity=3.2,
        ),
        Post(
            id="post_002",
            author_id="agent_tech",
            text="Just tested the new AI coding assistant. It writes better than me!",
            timestamp=now - timedelta(hours=5),
            has_media=False,
            likes=89,
            reshares=12,
            replies=34,
            velocity=1.5,
        ),
        Post(
            id="post_003",
            author_id="agent_food",
            text="Made the best sourdough bread today. The crust is perfect!",
            timestamp=now - timedelta(days=1),
            has_media=True,
            media_type="image",
            media_description="Golden brown sourdough loaf on cooling rack",
            likes=234,
            reshares=5,
            replies=67,
            velocity=0.8,
        ),
        Post(
            id="post_004",
            author_id="agent_crypto",
            text="Ethereum staking rewards are amazing. Passive income ftw!",
            timestamp=now - timedelta(hours=1),
            has_media=False,
            likes=78,
            reshares=22,
            replies=11,
            velocity=2.1,
        ),
        Post(
            id="post_005",
            author_id="agent_tech",
            text="The new smartphone camera is incredible. Night mode is magical.",
            timestamp=now - timedelta(hours=8),
            has_media=True,
            media_type="video",
            media_description="Video comparison of night mode photos",
            likes=312,
            reshares=89,
            replies=45,
            velocity=4.5,
        ),
        Post(
            id="post_006",
            author_id="agent_sports",
            text="What an incredible game last night! Championship vibes.",
            timestamp=now - timedelta(hours=12),
            has_media=True,
            media_type="gif",
            media_description="Highlight reel of winning play",
            likes=567,
            reshares=234,
            replies=189,
            velocity=6.2,
        ),
    ]


@pytest.mark.integration
class TestRAGFeedSystemIntegration:
    """Integration tests for the complete RAG feed system."""

    def test_full_workflow_preference_mode(self, sample_posts: list[Post]) -> None:
        """Test complete workflow: config → collection → retriever → feed → format."""
        # Create config with in-memory storage
        config = RAGConfig(
            collection_name="test_integration_pref",
            embedding_model="all-MiniLM-L6-v2",
            embedding_provider="sentence-transformers",
            persist_directory=None,
            feed_size=3,
            mode="preference",
        )

        # Create collection from config
        collection = create_collection(config)
        assert collection is not None
        assert collection.name == "test_integration_pref"

        # Create retriever
        retriever = FeedRetriever(
            collection=collection,
            feed_size=config.feed_size,
            default_mode=config.mode,
        )

        # Index sample posts
        retriever.add_posts(sample_posts)
        assert retriever.count() == len(sample_posts)

        # Retrieve feed with crypto/finance interests (preference mode)
        feed = retriever.get_feed(
            interests=["cryptocurrency", "bitcoin", "finance", "ethereum"],
            mode="preference",
        )

        # Verify feed properties
        assert len(feed) == config.feed_size
        assert all(isinstance(p, Post) for p in feed)

        # Crypto-related posts should be ranked higher due to interest similarity
        feed_texts = [p.text.lower() for p in feed]
        crypto_keywords = ["bitcoin", "ethereum", "crypto"]
        has_crypto_post = any(
            any(kw in text for kw in crypto_keywords) for text in feed_texts
        )
        assert has_crypto_post, "Expected crypto-related posts in preference feed"

        # Format feed for prompt
        now = datetime.now()
        formatted = format_feed_for_prompt(feed, now=now)

        # Verify formatted output structure
        assert formatted != ""
        assert "Post #1:" in formatted
        assert "Post #2:" in formatted
        assert "Post #3:" in formatted

        # Verify content is included
        for post in feed:
            assert post.text in formatted

        # Verify engagement stats format (number | number | number)
        assert " | " in formatted

        # Verify relative timestamp format
        assert "ago" in formatted or "just now" in formatted

    def test_full_workflow_random_mode(self, sample_posts: list[Post]) -> None:
        """Test complete workflow with random retrieval mode."""
        # Create config for random mode
        config = RAGConfig(
            collection_name="test_integration_random",
            embedding_model="all-MiniLM-L6-v2",
            embedding_provider="sentence-transformers",
            persist_directory=None,
            feed_size=3,
            mode="random",
        )

        # Create collection and retriever
        collection = create_collection(config)
        retriever = FeedRetriever(
            collection=collection,
            feed_size=config.feed_size,
            default_mode=config.mode,
        )

        # Index posts
        retriever.add_posts(sample_posts)

        # Retrieve random feed (no interests needed)
        feed = retriever.get_feed(mode="random")

        # Verify basic properties
        assert len(feed) == config.feed_size
        assert all(isinstance(p, Post) for p in feed)

        # Format and verify
        formatted = format_feed_for_prompt(feed)
        assert formatted != ""
        assert "Post #1:" in formatted

    def test_mode_switching(self, sample_posts: list[Post]) -> None:
        """Test switching between preference and random modes with same retriever."""
        config = RAGConfig(
            collection_name="test_integration_switch",
            feed_size=2,
            mode="preference",
        )

        collection = create_collection(config)
        retriever = FeedRetriever(
            collection=collection,
            feed_size=config.feed_size,
            default_mode=config.mode,
        )
        retriever.add_posts(sample_posts)

        # Get preference feed
        pref_feed = retriever.get_feed(
            interests=["technology", "AI", "coding"],
            mode="preference",
        )
        assert len(pref_feed) == 2

        # Get random feed
        random_feed = retriever.get_feed(mode="random")
        assert len(random_feed) == 2

        # Both should be valid Post lists
        assert all(isinstance(p, Post) for p in pref_feed)
        assert all(isinstance(p, Post) for p in random_feed)

    def test_media_indicators_in_formatted_output(
        self, sample_posts: list[Post]
    ) -> None:
        """Test that media indicators appear correctly in formatted output."""
        config = RAGConfig(
            collection_name="test_integration_media",
            feed_size=6,  # Get all posts
        )

        collection = create_collection(config)
        retriever = FeedRetriever(
            collection=collection,
            feed_size=config.feed_size,
            default_mode="random",
        )
        retriever.add_posts(sample_posts)

        # Get all posts
        feed = retriever.get_feed(mode="random")
        formatted = format_feed_for_prompt(feed)

        # Count media indicators
        media_posts = [p for p in feed if p.has_media]

        # Each media post should have an indicator in the output
        for post in media_posts:
            if post.media_type == "image":
                assert "IMAGE:" in formatted
            elif post.media_type == "video":
                assert "VIDEO:" in formatted
            elif post.media_type == "gif":
                assert "GIF:" in formatted

    def test_engagement_stats_in_formatted_output(
        self, sample_posts: list[Post]
    ) -> None:
        """Test that engagement stats appear in formatted output."""
        config = RAGConfig(
            collection_name="test_integration_stats",
            feed_size=3,
        )

        collection = create_collection(config)
        retriever = FeedRetriever(
            collection=collection,
            feed_size=config.feed_size,
            default_mode="random",
        )
        retriever.add_posts(sample_posts)

        feed = retriever.get_feed(mode="random")
        formatted = format_feed_for_prompt(feed)

        # Verify each post's stats appear
        for post in feed:
            # The format is: likes | reshares | replies | time
            assert str(post.likes) in formatted
            assert str(post.reshares) in formatted
            assert str(post.replies) in formatted

    def test_empty_collection_raises_error(self) -> None:
        """Test that retrieving from empty collection raises RuntimeError."""
        config = RAGConfig(
            collection_name="test_integration_empty",
            feed_size=3,
        )

        collection = create_collection(config)
        retriever = FeedRetriever(
            collection=collection,
            feed_size=config.feed_size,
            default_mode="random",
        )

        # Should raise when collection is empty
        with pytest.raises(RuntimeError, match="Collection is empty"):
            retriever.get_feed(mode="random")

    def test_fewer_posts_than_feed_size(self, sample_posts: list[Post]) -> None:
        """Test that feed returns all posts when fewer than feed_size exist."""
        config = RAGConfig(
            collection_name="test_integration_fewer",
            feed_size=10,  # More than sample_posts (6)
        )

        collection = create_collection(config)
        retriever = FeedRetriever(
            collection=collection,
            feed_size=config.feed_size,
            default_mode="random",
        )

        # Only add 2 posts
        retriever.add_posts(sample_posts[:2])

        feed = retriever.get_feed(mode="random")
        assert len(feed) == 2  # Should return all available posts
