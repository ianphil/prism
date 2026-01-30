"""Tests for RAGConfig Pydantic model."""

import pytest
from pydantic import ValidationError


class TestRAGConfig:
    """Test suite for RAGConfig model."""

    def test_default_values(self):
        """RAGConfig has sensible defaults."""
        from prism.rag.config import RAGConfig

        config = RAGConfig()

        assert config.collection_name == "posts"
        assert config.embedding_model == "all-MiniLM-L6-v2"
        assert config.embedding_provider == "sentence-transformers"
        assert config.persist_directory is None
        assert config.feed_size == 5
        assert config.mode == "preference"

    def test_custom_values(self):
        """RAGConfig accepts custom values."""
        from prism.rag.config import RAGConfig

        config = RAGConfig(
            collection_name="simulation_posts",
            embedding_model="nomic-embed-text",
            embedding_provider="ollama",
            persist_directory="./data/chromadb",
            feed_size=10,
            mode="random",
        )

        assert config.collection_name == "simulation_posts"
        assert config.embedding_model == "nomic-embed-text"
        assert config.embedding_provider == "ollama"
        assert config.persist_directory == "./data/chromadb"
        assert config.feed_size == 10
        assert config.mode == "random"

    def test_feed_size_minimum(self):
        """feed_size must be at least 1."""
        from prism.rag.config import RAGConfig

        with pytest.raises(ValidationError) as exc_info:
            RAGConfig(feed_size=0)

        assert "feed_size" in str(exc_info.value)

    def test_feed_size_maximum(self):
        """feed_size must be at most 20."""
        from prism.rag.config import RAGConfig

        with pytest.raises(ValidationError) as exc_info:
            RAGConfig(feed_size=21)

        assert "feed_size" in str(exc_info.value)

    def test_feed_size_valid_range(self):
        """feed_size at boundaries is valid."""
        from prism.rag.config import RAGConfig

        config_min = RAGConfig(feed_size=1)
        config_max = RAGConfig(feed_size=20)

        assert config_min.feed_size == 1
        assert config_max.feed_size == 20

    def test_invalid_mode(self):
        """Invalid mode raises validation error."""
        from prism.rag.config import RAGConfig

        with pytest.raises(ValidationError) as exc_info:
            RAGConfig(mode="hybrid")

        assert "mode" in str(exc_info.value)

    def test_valid_modes(self):
        """Both valid modes are accepted."""
        from prism.rag.config import RAGConfig

        config_pref = RAGConfig(mode="preference")
        config_rand = RAGConfig(mode="random")

        assert config_pref.mode == "preference"
        assert config_rand.mode == "random"

    def test_invalid_embedding_provider(self):
        """Invalid embedding_provider raises validation error."""
        from prism.rag.config import RAGConfig

        with pytest.raises(ValidationError) as exc_info:
            RAGConfig(embedding_provider="openai")

        assert "embedding_provider" in str(exc_info.value)

    def test_valid_embedding_providers(self):
        """Both valid embedding providers are accepted."""
        from prism.rag.config import RAGConfig

        config_st = RAGConfig(embedding_provider="sentence-transformers")
        config_ol = RAGConfig(embedding_provider="ollama")

        assert config_st.embedding_provider == "sentence-transformers"
        assert config_ol.embedding_provider == "ollama"


class TestPrismConfigIntegration:
    """Test RAGConfig integration with PrismConfig."""

    def test_prism_config_has_rag_section(self):
        """PrismConfig includes a rag field of type RAGConfig."""
        from prism.llm.config import PrismConfig
        from prism.rag.config import RAGConfig

        config = PrismConfig()

        assert hasattr(config, "rag")
        assert isinstance(config.rag, RAGConfig)

    def test_prism_config_rag_defaults(self):
        """PrismConfig rag section has default RAGConfig values."""
        from prism.llm.config import PrismConfig

        config = PrismConfig()

        assert config.rag.collection_name == "posts"
        assert config.rag.feed_size == 5
        assert config.rag.mode == "preference"

    def test_prism_config_custom_rag(self):
        """PrismConfig accepts custom rag configuration."""
        from prism.llm.config import PrismConfig
        from prism.rag.config import RAGConfig

        config = PrismConfig(
            rag=RAGConfig(
                collection_name="custom_posts",
                feed_size=10,
                mode="random",
            )
        )

        assert config.rag.collection_name == "custom_posts"
        assert config.rag.feed_size == 10
        assert config.rag.mode == "random"

    def test_load_config_includes_rag(self):
        """load_config loads RAG section from YAML."""
        from prism.llm.config import load_config

        config = load_config("configs/default.yaml")

        # Verify RAG section is loaded (with whatever values are in file)
        assert hasattr(config, "rag")
        assert config.rag.collection_name is not None
        assert config.rag.feed_size >= 1
        assert config.rag.mode in ("preference", "random")
