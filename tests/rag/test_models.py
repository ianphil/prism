"""Tests for Post Pydantic model."""

from datetime import datetime

import pytest
from pydantic import ValidationError


class TestPostModel:
    """Test suite for Post model."""

    def test_post_with_all_fields(self):
        """Post can be created with all fields."""
        from prism.rag.models import Post

        post = Post(
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

        assert post.id == "post_001"
        assert post.author_id == "agent_42"
        assert post.text == "My local coffee shop now accepts Bitcoin!"
        assert post.timestamp == datetime(2026, 1, 29, 10, 30, 0)
        assert post.has_media is True
        assert post.media_type == "image"
        assert post.media_description == "Bitcoin payment terminal at counter"
        assert post.likes == 89
        assert post.reshares == 34
        assert post.replies == 12
        assert post.velocity == 2.5

    def test_post_with_minimal_fields(self):
        """Post can be created with only required fields."""
        from prism.rag.models import Post

        post = Post(
            id="post_002",
            author_id="agent_1",
            text="Hello world",
            timestamp=datetime(2026, 1, 29, 12, 0, 0),
        )

        assert post.id == "post_002"
        assert post.has_media is False
        assert post.media_type is None
        assert post.media_description is None
        assert post.likes == 0
        assert post.reshares == 0
        assert post.replies == 0
        assert post.velocity == 0.0

    def test_post_negative_likes_raises_error(self):
        """Negative likes raises validation error."""
        from prism.rag.models import Post

        with pytest.raises(ValidationError) as exc_info:
            Post(
                id="post_003",
                author_id="agent_1",
                text="Test post",
                timestamp=datetime.now(),
                likes=-5,
            )

        assert "likes" in str(exc_info.value)

    def test_post_negative_reshares_raises_error(self):
        """Negative reshares raises validation error."""
        from prism.rag.models import Post

        with pytest.raises(ValidationError) as exc_info:
            Post(
                id="post_003",
                author_id="agent_1",
                text="Test post",
                timestamp=datetime.now(),
                reshares=-1,
            )

        assert "reshares" in str(exc_info.value)

    def test_post_negative_replies_raises_error(self):
        """Negative replies raises validation error."""
        from prism.rag.models import Post

        with pytest.raises(ValidationError) as exc_info:
            Post(
                id="post_003",
                author_id="agent_1",
                text="Test post",
                timestamp=datetime.now(),
                replies=-10,
            )

        assert "replies" in str(exc_info.value)

    def test_post_negative_velocity_raises_error(self):
        """Negative velocity raises validation error."""
        from prism.rag.models import Post

        with pytest.raises(ValidationError) as exc_info:
            Post(
                id="post_003",
                author_id="agent_1",
                text="Test post",
                timestamp=datetime.now(),
                velocity=-0.5,
            )

        assert "velocity" in str(exc_info.value)

    def test_post_invalid_media_type_raises_error(self):
        """Invalid media_type raises validation error."""
        from prism.rag.models import Post

        with pytest.raises(ValidationError) as exc_info:
            Post(
                id="post_003",
                author_id="agent_1",
                text="Test post",
                timestamp=datetime.now(),
                has_media=True,
                media_type="audio",  # Invalid - only image, video, gif allowed
            )

        assert "media_type" in str(exc_info.value)

    def test_post_valid_media_types(self):
        """All valid media types are accepted."""
        from prism.rag.models import Post

        for media_type in ["image", "video", "gif"]:
            post = Post(
                id=f"post_{media_type}",
                author_id="agent_1",
                text="Test post",
                timestamp=datetime.now(),
                has_media=True,
                media_type=media_type,
            )
            assert post.media_type == media_type


class TestPostMediaConsistency:
    """Test suite for Post media_type/has_media consistency validation."""

    def test_has_media_false_media_type_none_is_valid(self):
        """has_media=False with media_type=None is valid."""
        from prism.rag.models import Post

        post = Post(
            id="post_1",
            author_id="agent_1",
            text="Test post",
            timestamp=datetime.now(),
            has_media=False,
            media_type=None,
        )
        assert post.has_media is False
        assert post.media_type is None

    def test_has_media_true_with_media_type_is_valid(self):
        """has_media=True with media_type set is valid."""
        from prism.rag.models import Post

        post = Post(
            id="post_1",
            author_id="agent_1",
            text="Test post",
            timestamp=datetime.now(),
            has_media=True,
            media_type="image",
        )
        assert post.has_media is True
        assert post.media_type == "image"

    def test_has_media_false_with_media_type_raises_error(self):
        """has_media=False with media_type set raises ValueError."""
        from prism.rag.models import Post

        with pytest.raises(ValidationError) as exc_info:
            Post(
                id="post_1",
                author_id="agent_1",
                text="Test post",
                timestamp=datetime.now(),
                has_media=False,
                media_type="image",
            )

        assert "media_type cannot be set when has_media is False" in str(exc_info.value)

    def test_has_media_true_media_type_none_is_valid(self):
        """has_media=True with media_type=None is valid (media type unspecified)."""
        from prism.rag.models import Post

        post = Post(
            id="post_1",
            author_id="agent_1",
            text="Test post",
            timestamp=datetime.now(),
            has_media=True,
            media_type=None,
        )
        assert post.has_media is True
        assert post.media_type is None


class TestPostChromaConversion:
    """Test suite for Post ChromaDB conversion methods."""

    def test_to_metadata_returns_dict(self):
        """to_metadata returns a dict with all fields."""
        from prism.rag.models import Post

        post = Post(
            id="post_001",
            author_id="agent_42",
            text="Test post content",
            timestamp=datetime(2026, 1, 29, 10, 30, 0),
            has_media=True,
            media_type="image",
            media_description="A test image",
            likes=10,
            reshares=5,
            replies=3,
            velocity=1.5,
        )

        metadata = post.to_metadata()

        assert isinstance(metadata, dict)
        assert metadata["author_id"] == "agent_42"
        assert metadata["timestamp"] == "2026-01-29T10:30:00"
        assert metadata["has_media"] is True
        assert metadata["media_type"] == "image"
        assert metadata["media_description"] == "A test image"
        assert metadata["likes"] == 10
        assert metadata["reshares"] == 5
        assert metadata["replies"] == 3
        assert metadata["velocity"] == 1.5

    def test_to_metadata_excludes_id_and_text(self):
        """to_metadata does not include id and text (stored separately in ChromaDB)."""
        from prism.rag.models import Post

        post = Post(
            id="post_001",
            author_id="agent_1",
            text="Test content",
            timestamp=datetime.now(),
        )

        metadata = post.to_metadata()

        assert "id" not in metadata
        assert "text" not in metadata

    def test_from_chroma_result_reconstructs_post(self):
        """from_chroma_result correctly reconstructs a Post."""
        from prism.rag.models import Post

        result_id = "post_001"
        result_document = "Original post text"
        result_metadata = {
            "author_id": "agent_42",
            "timestamp": "2026-01-29T10:30:00",
            "has_media": True,
            "media_type": "image",
            "media_description": "Test image description",
            "likes": 89,
            "reshares": 34,
            "replies": 12,
            "velocity": 2.5,
        }

        post = Post.from_chroma_result(
            id=result_id,
            document=result_document,
            metadata=result_metadata,
        )

        assert post.id == "post_001"
        assert post.text == "Original post text"
        assert post.author_id == "agent_42"
        assert post.timestamp == datetime(2026, 1, 29, 10, 30, 0)
        assert post.has_media is True
        assert post.media_type == "image"
        assert post.media_description == "Test image description"
        assert post.likes == 89
        assert post.reshares == 34
        assert post.replies == 12
        assert post.velocity == 2.5

    def test_from_chroma_result_with_minimal_metadata(self):
        """from_chroma_result handles minimal metadata with defaults."""
        from prism.rag.models import Post

        result_metadata = {
            "author_id": "agent_1",
            "timestamp": "2026-01-29T12:00:00",
        }

        post = Post.from_chroma_result(
            id="post_002",
            document="Simple post",
            metadata=result_metadata,
        )

        assert post.id == "post_002"
        assert post.has_media is False
        assert post.media_type is None
        assert post.likes == 0
        assert post.reshares == 0
        assert post.replies == 0
        assert post.velocity == 0.0

    def test_roundtrip_conversion(self):
        """Post survives roundtrip through to_metadata and from_chroma_result."""
        from prism.rag.models import Post

        original = Post(
            id="post_roundtrip",
            author_id="agent_test",
            text="Roundtrip test content",
            timestamp=datetime(2026, 1, 29, 15, 45, 30),
            has_media=True,
            media_type="video",
            media_description="A video clip",
            likes=100,
            reshares=50,
            replies=25,
            velocity=5.0,
        )

        metadata = original.to_metadata()
        reconstructed = Post.from_chroma_result(
            id=original.id,
            document=original.text,
            metadata=metadata,
        )

        assert reconstructed == original
