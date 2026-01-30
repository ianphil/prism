"""Tests for FeedRetriever class."""

import uuid
from datetime import datetime

import chromadb
import pytest
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from prism.rag.models import Post
from prism.rag.retriever import FeedRetriever


@pytest.fixture
def embedding_function():
    """Create a sentence-transformer embedding function for tests."""
    return SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")


@pytest.fixture
def collection(embedding_function):
    """Create a fresh in-memory ChromaDB collection for each test."""
    client = chromadb.Client()
    # Use unique collection name for each test to avoid conflicts
    collection_name = f"test_posts_{uuid.uuid4().hex[:8]}"
    return client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_function,
    )


@pytest.fixture
def sample_post():
    """Create a sample post for testing."""
    return Post(
        id="post_001",
        author_id="agent_42",
        text="My local coffee shop now accepts Bitcoin!",
        timestamp=datetime(2026, 1, 29, 10, 30, 0),
        has_media=True,
        media_type="image",
        media_description="Bitcoin payment terminal at counter",
        likes=89,
        reshares=34,
        replies=12,
        velocity=2.5,
    )


@pytest.fixture
def sample_posts():
    """Create a list of sample posts for testing."""
    return [
        Post(
            id="post_001",
            author_id="agent_1",
            text="Bitcoin and crypto are the future of finance!",
            timestamp=datetime(2026, 1, 29, 10, 0, 0),
            likes=100,
        ),
        Post(
            id="post_002",
            author_id="agent_2",
            text="Just adopted a cute puppy from the shelter!",
            timestamp=datetime(2026, 1, 29, 11, 0, 0),
            has_media=True,
            media_type="image",
            media_description="Golden retriever puppy",
            likes=250,
        ),
        Post(
            id="post_003",
            author_id="agent_3",
            text="New AI model released, impressive capabilities in coding",
            timestamp=datetime(2026, 1, 29, 12, 0, 0),
            likes=75,
        ),
        Post(
            id="post_004",
            author_id="agent_4",
            text="Ethereum smart contracts are revolutionizing DeFi",
            timestamp=datetime(2026, 1, 29, 13, 0, 0),
            likes=60,
        ),
        Post(
            id="post_005",
            author_id="agent_5",
            text="Beautiful sunset at the beach today",
            timestamp=datetime(2026, 1, 29, 14, 0, 0),
            has_media=True,
            media_type="image",
            media_description="Orange sunset over ocean waves",
            likes=180,
        ),
    ]


class TestFeedRetrieverInit:
    """Tests for FeedRetriever.__init__()"""

    def test_accepts_collection_and_config(self, collection):
        """FeedRetriever accepts a collection and optional config."""
        retriever = FeedRetriever(collection=collection)
        assert retriever is not None

    def test_stores_feed_size(self, collection):
        """FeedRetriever stores the configured feed_size."""
        retriever = FeedRetriever(collection=collection, feed_size=10)
        assert retriever._feed_size == 10

    def test_stores_default_mode(self, collection):
        """FeedRetriever stores the configured default_mode."""
        retriever = FeedRetriever(collection=collection, default_mode="random")
        assert retriever._default_mode == "random"

    def test_default_feed_size_is_5(self, collection):
        """FeedRetriever defaults to feed_size=5."""
        retriever = FeedRetriever(collection=collection)
        assert retriever._feed_size == 5

    def test_default_mode_is_preference(self, collection):
        """FeedRetriever defaults to mode='preference'."""
        retriever = FeedRetriever(collection=collection)
        assert retriever._default_mode == "preference"

    def test_stores_collection_reference(self, collection):
        """FeedRetriever stores a reference to the collection."""
        retriever = FeedRetriever(collection=collection)
        assert retriever._collection is collection


class TestFeedRetrieverAddPost:
    """Tests for FeedRetriever.add_post()"""

    def test_indexes_single_post(self, collection, sample_post):
        """add_post indexes a single post in the collection."""
        retriever = FeedRetriever(collection=collection)
        retriever.add_post(sample_post)

        # Verify post was indexed
        result = collection.get(ids=[sample_post.id])
        assert len(result["ids"]) == 1
        assert result["ids"][0] == sample_post.id

    def test_stores_post_text_as_document(self, collection, sample_post):
        """add_post stores post.text as the document for embedding."""
        retriever = FeedRetriever(collection=collection)
        retriever.add_post(sample_post)

        result = collection.get(ids=[sample_post.id], include=["documents"])
        assert result["documents"][0] == sample_post.text

    def test_stores_metadata_correctly(self, collection, sample_post):
        """add_post stores post metadata correctly."""
        retriever = FeedRetriever(collection=collection)
        retriever.add_post(sample_post)

        result = collection.get(ids=[sample_post.id], include=["metadatas"])
        metadata = result["metadatas"][0]

        assert metadata["author_id"] == sample_post.author_id
        assert metadata["has_media"] == sample_post.has_media
        assert metadata["media_type"] == sample_post.media_type
        assert metadata["likes"] == sample_post.likes
        assert metadata["reshares"] == sample_post.reshares
        assert metadata["replies"] == sample_post.replies

    def test_upsert_semantics(self, collection, sample_post):
        """add_post uses upsert semantics (update if exists)."""
        retriever = FeedRetriever(collection=collection)

        # Add post first time
        retriever.add_post(sample_post)

        # Update likes and add again
        updated_post = sample_post.model_copy(update={"likes": 200})
        retriever.add_post(updated_post)

        # Should still be one post with updated likes
        result = collection.get(ids=[sample_post.id], include=["metadatas"])
        assert len(result["ids"]) == 1
        assert result["metadatas"][0]["likes"] == 200


class TestFeedRetrieverAddPosts:
    """Tests for FeedRetriever.add_posts()"""

    def test_batch_indexes_multiple_posts(self, collection, sample_posts):
        """add_posts batch indexes multiple posts."""
        retriever = FeedRetriever(collection=collection)
        retriever.add_posts(sample_posts)

        # Verify all posts were indexed
        result = collection.get()
        assert len(result["ids"]) == len(sample_posts)

    def test_all_posts_retrievable_after_indexing(self, collection, sample_posts):
        """All posts are retrievable after batch indexing."""
        retriever = FeedRetriever(collection=collection)
        retriever.add_posts(sample_posts)

        # Retrieve each post by ID
        for post in sample_posts:
            result = collection.get(ids=[post.id], include=["documents", "metadatas"])
            assert len(result["ids"]) == 1
            assert result["documents"][0] == post.text
            assert result["metadatas"][0]["author_id"] == post.author_id

    def test_empty_list_is_no_op(self, collection):
        """add_posts with empty list does nothing."""
        retriever = FeedRetriever(collection=collection)
        retriever.add_posts([])

        result = collection.get()
        assert len(result["ids"]) == 0


class TestFeedRetrieverPreferenceMode:
    """Tests for FeedRetriever.get_feed(mode='preference')"""

    def test_returns_list_of_posts(self, collection, sample_posts):
        """get_feed returns a list of Post objects."""
        retriever = FeedRetriever(collection=collection, feed_size=3)
        retriever.add_posts(sample_posts)

        feed = retriever.get_feed(interests=["crypto", "bitcoin"], mode="preference")

        assert isinstance(feed, list)
        assert all(isinstance(p, Post) for p in feed)

    def test_relevant_posts_ranked_higher(self, collection, sample_posts):
        """Preference mode returns crypto posts first for crypto interests."""
        retriever = FeedRetriever(collection=collection, feed_size=3)
        retriever.add_posts(sample_posts)

        feed = retriever.get_feed(
            interests=["crypto", "bitcoin", "finance"], mode="preference"
        )

        # The first posts should be crypto-related (post_001 and post_004)
        feed_ids = [p.id for p in feed]
        # At minimum, crypto posts should be in the top results
        crypto_ids = {"post_001", "post_004"}
        assert any(
            pid in crypto_ids for pid in feed_ids[:2]
        ), f"Expected crypto posts in top 2, got {feed_ids}"

    def test_respects_feed_size_limit(self, collection, sample_posts):
        """get_feed returns at most feed_size posts."""
        retriever = FeedRetriever(collection=collection, feed_size=2)
        retriever.add_posts(sample_posts)

        feed = retriever.get_feed(interests=["anything"], mode="preference")

        assert len(feed) <= 2

    def test_raises_error_if_interests_is_none(self, collection, sample_posts):
        """get_feed raises ValueError if interests is None in preference mode."""
        retriever = FeedRetriever(collection=collection)
        retriever.add_posts(sample_posts)

        with pytest.raises(ValueError, match="interests required"):
            retriever.get_feed(interests=None, mode="preference")

    def test_raises_error_if_interests_is_empty(self, collection, sample_posts):
        """get_feed raises ValueError if interests is empty list in preference mode."""
        retriever = FeedRetriever(collection=collection)
        retriever.add_posts(sample_posts)

        with pytest.raises(ValueError, match="interests required"):
            retriever.get_feed(interests=[], mode="preference")

    def test_uses_default_mode_when_mode_is_none(self, collection, sample_posts):
        """get_feed uses default_mode when mode parameter is None."""
        retriever = FeedRetriever(
            collection=collection, feed_size=3, default_mode="preference"
        )
        retriever.add_posts(sample_posts)

        # Should use preference mode (default), requiring interests
        with pytest.raises(ValueError, match="interests required"):
            retriever.get_feed(interests=None, mode=None)

    def test_reconstructs_post_metadata(self, collection, sample_posts):
        """Retrieved posts have correct metadata from ChromaDB."""
        retriever = FeedRetriever(collection=collection, feed_size=5)
        retriever.add_posts(sample_posts)

        feed = retriever.get_feed(interests=["puppy", "dog", "pet"], mode="preference")

        # Find the puppy post in the feed
        puppy_posts = [p for p in feed if "puppy" in p.text.lower()]
        if puppy_posts:
            puppy_post = puppy_posts[0]
            assert puppy_post.has_media is True
            assert puppy_post.media_type == "image"
            assert puppy_post.likes == 250


class TestFeedRetrieverRandomMode:
    """Tests for FeedRetriever.get_feed(mode='random')"""

    def test_returns_list_of_posts(self, collection, sample_posts):
        """get_feed in random mode returns a list of Post objects."""
        retriever = FeedRetriever(collection=collection, feed_size=3)
        retriever.add_posts(sample_posts)

        feed = retriever.get_feed(mode="random")

        assert isinstance(feed, list)
        assert all(isinstance(p, Post) for p in feed)

    def test_does_not_require_interests(self, collection, sample_posts):
        """Random mode does not require interests parameter."""
        retriever = FeedRetriever(collection=collection, feed_size=3)
        retriever.add_posts(sample_posts)

        # Should not raise - interests not required for random mode
        feed = retriever.get_feed(interests=None, mode="random")
        assert len(feed) > 0

    def test_returns_diverse_posts(self, collection, sample_posts):
        """Random mode returns different subsets of posts across calls."""
        # Use feed_size=3 so we sample 3 from 5, giving actual randomness
        retriever = FeedRetriever(collection=collection, feed_size=3)
        retriever.add_posts(sample_posts)

        # Run multiple retrievals and collect all selected ID sets
        selected_sets = set()
        for _ in range(20):
            feed = retriever.get_feed(mode="random")
            if feed:
                # Use frozenset since order within get() result may be consistent
                selected = frozenset(p.id for p in feed)
                selected_sets.add(selected)

        # With 20 runs and C(5,3)=10 possible combinations, we should see variation
        # Note: This test is probabilistic but very likely to pass
        assert (
            len(selected_sets) >= 2
        ), f"Expected diverse selections, but always got the same: {selected_sets}"

    def test_respects_feed_size_limit(self, collection, sample_posts):
        """Random mode respects feed_size limit."""
        retriever = FeedRetriever(collection=collection, feed_size=2)
        retriever.add_posts(sample_posts)

        feed = retriever.get_feed(mode="random")

        assert len(feed) <= 2

    def test_returns_valid_posts(self, collection, sample_posts):
        """Random mode returns valid Post objects with correct data."""
        retriever = FeedRetriever(collection=collection, feed_size=5)
        retriever.add_posts(sample_posts)

        feed = retriever.get_feed(mode="random")

        # All returned posts should be from our original sample
        sample_ids = {p.id for p in sample_posts}
        for post in feed:
            assert post.id in sample_ids
            assert post.text  # Non-empty text
            assert post.author_id  # Non-empty author

    def test_default_mode_random_works(self, collection, sample_posts):
        """FeedRetriever with default_mode='random' works without interests."""
        retriever = FeedRetriever(
            collection=collection, feed_size=3, default_mode="random"
        )
        retriever.add_posts(sample_posts)

        # Should use random mode by default
        feed = retriever.get_feed()  # No interests, no mode specified
        assert len(feed) > 0


class TestFeedRetrieverEdgeCases:
    """Tests for edge cases and helper methods."""

    def test_empty_collection_raises_runtime_error_preference(self, collection):
        """get_feed raises RuntimeError on empty collection (preference mode)."""
        retriever = FeedRetriever(collection=collection)

        with pytest.raises(RuntimeError, match="Collection is empty"):
            retriever.get_feed(interests=["crypto"], mode="preference")

    def test_empty_collection_raises_runtime_error_random(self, collection):
        """get_feed raises RuntimeError on empty collection (random mode)."""
        retriever = FeedRetriever(collection=collection)

        with pytest.raises(RuntimeError, match="Collection is empty"):
            retriever.get_feed(mode="random")

    def test_fewer_posts_than_feed_size_returns_all(self, collection):
        """When collection has fewer posts than feed_size, return all available."""
        retriever = FeedRetriever(collection=collection, feed_size=10)

        # Add only 3 posts
        posts = [
            Post(
                id=f"post_{i}",
                author_id=f"agent_{i}",
                text=f"Post number {i}",
                timestamp=datetime(2026, 1, 29, i, 0, 0),
            )
            for i in range(3)
        ]
        retriever.add_posts(posts)

        feed = retriever.get_feed(interests=["post"], mode="preference")
        assert len(feed) == 3  # All available, not 10

    def test_fewer_posts_than_feed_size_random(self, collection):
        """When collection has fewer posts than feed_size, random mode returns all."""
        retriever = FeedRetriever(collection=collection, feed_size=10)

        # Add only 2 posts
        posts = [
            Post(
                id=f"post_{i}",
                author_id=f"agent_{i}",
                text=f"Post number {i}",
                timestamp=datetime(2026, 1, 29, i, 0, 0),
            )
            for i in range(2)
        ]
        retriever.add_posts(posts)

        feed = retriever.get_feed(mode="random")
        assert len(feed) == 2  # All available, not 10

    def test_count_returns_correct_number(self, collection, sample_posts):
        """count() returns the number of indexed posts."""
        retriever = FeedRetriever(collection=collection)

        assert retriever.count() == 0

        retriever.add_posts(sample_posts)
        assert retriever.count() == len(sample_posts)

    def test_count_empty_collection(self, collection):
        """count() returns 0 for empty collection."""
        retriever = FeedRetriever(collection=collection)
        assert retriever.count() == 0

    def test_clear_removes_all_posts(self, collection, sample_posts):
        """clear() removes all posts from the collection."""
        retriever = FeedRetriever(collection=collection)
        retriever.add_posts(sample_posts)

        assert retriever.count() == len(sample_posts)

        retriever.clear()

        assert retriever.count() == 0

    def test_clear_empty_collection_is_no_op(self, collection):
        """clear() on empty collection does nothing (no error)."""
        retriever = FeedRetriever(collection=collection)

        # Should not raise
        retriever.clear()
        assert retriever.count() == 0

    def test_single_post_retrieval(self, collection, sample_post):
        """Retriever works with a single post."""
        retriever = FeedRetriever(collection=collection, feed_size=5)
        retriever.add_post(sample_post)

        # Preference mode
        feed = retriever.get_feed(interests=["bitcoin"], mode="preference")
        assert len(feed) == 1
        assert feed[0].id == sample_post.id

        # Random mode
        feed = retriever.get_feed(mode="random")
        assert len(feed) == 1
        assert feed[0].id == sample_post.id
