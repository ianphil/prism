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


# =============================================================================
# Feature 005: X Algorithm Ranking - RankingConfig
# =============================================================================


class TestRankingConfigMode:
    """Tests for RankingConfig.mode field (T011)."""

    def test_ranking_config_mode_default_is_preference(self):
        """RankingConfig mode defaults to 'preference'."""
        from prism.rag.config import RankingConfig

        config = RankingConfig()
        assert config.mode == "preference"

    def test_ranking_config_mode_accepts_x_algo(self):
        """RankingConfig mode accepts 'x_algo'."""
        from prism.rag.config import RankingConfig

        config = RankingConfig(mode="x_algo")
        assert config.mode == "x_algo"

    def test_ranking_config_mode_accepts_preference(self):
        """RankingConfig mode accepts 'preference'."""
        from prism.rag.config import RankingConfig

        config = RankingConfig(mode="preference")
        assert config.mode == "preference"

    def test_ranking_config_mode_accepts_random(self):
        """RankingConfig mode accepts 'random'."""
        from prism.rag.config import RankingConfig

        config = RankingConfig(mode="random")
        assert config.mode == "random"

    def test_ranking_config_mode_rejects_invalid(self):
        """RankingConfig mode rejects invalid values."""
        from prism.rag.config import RankingConfig

        with pytest.raises(ValidationError) as exc_info:
            RankingConfig(mode="invalid_mode")

        assert "mode" in str(exc_info.value)


class TestRankingConfigOutOfNetworkScale:
    """Tests for RankingConfig.out_of_network_scale field (T013)."""

    def test_out_of_network_scale_default_is_0_75(self):
        """out_of_network_scale defaults to 0.75."""
        from prism.rag.config import RankingConfig

        config = RankingConfig()
        assert config.out_of_network_scale == 0.75

    def test_out_of_network_scale_accepts_valid_values(self):
        """out_of_network_scale accepts values in [0.0, 1.0]."""
        from prism.rag.config import RankingConfig

        config_min = RankingConfig(out_of_network_scale=0.0)
        config_mid = RankingConfig(out_of_network_scale=0.5)
        config_max = RankingConfig(out_of_network_scale=1.0)

        assert config_min.out_of_network_scale == 0.0
        assert config_mid.out_of_network_scale == 0.5
        assert config_max.out_of_network_scale == 1.0

    def test_out_of_network_scale_rejects_negative(self):
        """out_of_network_scale rejects values < 0.0."""
        from prism.rag.config import RankingConfig

        with pytest.raises(ValidationError) as exc_info:
            RankingConfig(out_of_network_scale=-0.1)

        assert "out_of_network_scale" in str(exc_info.value)

    def test_out_of_network_scale_rejects_above_one(self):
        """out_of_network_scale rejects values > 1.0."""
        from prism.rag.config import RankingConfig

        with pytest.raises(ValidationError) as exc_info:
            RankingConfig(out_of_network_scale=1.1)

        assert "out_of_network_scale" in str(exc_info.value)


class TestRankingConfigReplyScale:
    """Tests for RankingConfig.reply_scale field (T015)."""

    def test_reply_scale_default_is_0_75(self):
        """reply_scale defaults to 0.75."""
        from prism.rag.config import RankingConfig

        config = RankingConfig()
        assert config.reply_scale == 0.75

    def test_reply_scale_accepts_valid_values(self):
        """reply_scale accepts values in [0.0, 1.0]."""
        from prism.rag.config import RankingConfig

        config_min = RankingConfig(reply_scale=0.0)
        config_mid = RankingConfig(reply_scale=0.5)
        config_max = RankingConfig(reply_scale=1.0)

        assert config_min.reply_scale == 0.0
        assert config_mid.reply_scale == 0.5
        assert config_max.reply_scale == 1.0

    def test_reply_scale_rejects_negative(self):
        """reply_scale rejects values < 0.0."""
        from prism.rag.config import RankingConfig

        with pytest.raises(ValidationError) as exc_info:
            RankingConfig(reply_scale=-0.1)

        assert "reply_scale" in str(exc_info.value)

    def test_reply_scale_rejects_above_one(self):
        """reply_scale rejects values > 1.0."""
        from prism.rag.config import RankingConfig

        with pytest.raises(ValidationError) as exc_info:
            RankingConfig(reply_scale=1.1)

        assert "reply_scale" in str(exc_info.value)


class TestRankingConfigAuthorDiversityDecay:
    """Tests for RankingConfig.author_diversity_decay field (T017)."""

    def test_author_diversity_decay_default_is_0_5(self):
        """author_diversity_decay defaults to 0.5."""
        from prism.rag.config import RankingConfig

        config = RankingConfig()
        assert config.author_diversity_decay == 0.5

    def test_author_diversity_decay_accepts_valid_values(self):
        """author_diversity_decay accepts values in [0.0, 1.0]."""
        from prism.rag.config import RankingConfig

        # Note: floor must be <= decay, so set floor=0.0 when decay=0.0
        config_min = RankingConfig(
            author_diversity_decay=0.0, author_diversity_floor=0.0
        )
        config_mid = RankingConfig(author_diversity_decay=0.7)
        config_max = RankingConfig(author_diversity_decay=1.0)

        assert config_min.author_diversity_decay == 0.0
        assert config_mid.author_diversity_decay == 0.7
        assert config_max.author_diversity_decay == 1.0

    def test_author_diversity_decay_rejects_negative(self):
        """author_diversity_decay rejects values < 0.0."""
        from prism.rag.config import RankingConfig

        with pytest.raises(ValidationError) as exc_info:
            RankingConfig(author_diversity_decay=-0.1)

        assert "author_diversity_decay" in str(exc_info.value)

    def test_author_diversity_decay_rejects_above_one(self):
        """author_diversity_decay rejects values > 1.0."""
        from prism.rag.config import RankingConfig

        with pytest.raises(ValidationError) as exc_info:
            RankingConfig(author_diversity_decay=1.1)

        assert "author_diversity_decay" in str(exc_info.value)


class TestRankingConfigAuthorDiversityFloor:
    """Tests for RankingConfig.author_diversity_floor field (T019)."""

    def test_author_diversity_floor_default_is_0_25(self):
        """author_diversity_floor defaults to 0.25."""
        from prism.rag.config import RankingConfig

        config = RankingConfig()
        assert config.author_diversity_floor == 0.25

    def test_author_diversity_floor_accepts_valid_values(self):
        """author_diversity_floor accepts values in [0.0, 1.0]."""
        from prism.rag.config import RankingConfig

        config_min = RankingConfig(
            author_diversity_floor=0.0, author_diversity_decay=0.5
        )
        config_mid = RankingConfig(
            author_diversity_floor=0.3, author_diversity_decay=0.5
        )
        config_max = RankingConfig(
            author_diversity_floor=0.5, author_diversity_decay=0.5
        )

        assert config_min.author_diversity_floor == 0.0
        assert config_mid.author_diversity_floor == 0.3
        assert config_max.author_diversity_floor == 0.5

    def test_author_diversity_floor_rejects_negative(self):
        """author_diversity_floor rejects values < 0.0."""
        from prism.rag.config import RankingConfig

        with pytest.raises(ValidationError) as exc_info:
            RankingConfig(author_diversity_floor=-0.1)

        assert "author_diversity_floor" in str(exc_info.value)

    def test_author_diversity_floor_rejects_above_one(self):
        """author_diversity_floor rejects values > 1.0."""
        from prism.rag.config import RankingConfig

        with pytest.raises(ValidationError) as exc_info:
            RankingConfig(author_diversity_floor=1.1)

        assert "author_diversity_floor" in str(exc_info.value)


class TestRankingConfigFloorDecayConstraint:
    """Tests for floor <= decay constraint (T021)."""

    def test_floor_greater_than_decay_raises_error(self):
        """author_diversity_floor > author_diversity_decay raises ValidationError."""
        from prism.rag.config import RankingConfig

        with pytest.raises(ValidationError) as exc_info:
            RankingConfig(
                author_diversity_decay=0.3,
                author_diversity_floor=0.5,  # floor > decay
            )

        error_msg = str(exc_info.value)
        assert "author_diversity_floor" in error_msg or "floor" in error_msg.lower()

    def test_floor_equal_to_decay_is_valid(self):
        """author_diversity_floor == author_diversity_decay is valid."""
        from prism.rag.config import RankingConfig

        config = RankingConfig(
            author_diversity_decay=0.5,
            author_diversity_floor=0.5,
        )

        assert config.author_diversity_floor == 0.5
        assert config.author_diversity_decay == 0.5

    def test_floor_less_than_decay_is_valid(self):
        """author_diversity_floor < author_diversity_decay is valid."""
        from prism.rag.config import RankingConfig

        config = RankingConfig(
            author_diversity_decay=0.8,
            author_diversity_floor=0.2,
        )

        assert config.author_diversity_floor == 0.2
        assert config.author_diversity_decay == 0.8


class TestRankingConfigCandidateLimits:
    """Tests for RankingConfig candidate limit fields (T023)."""

    def test_in_network_limit_default_is_50(self):
        """in_network_limit defaults to 50."""
        from prism.rag.config import RankingConfig

        config = RankingConfig()
        assert config.in_network_limit == 50

    def test_out_of_network_limit_default_is_50(self):
        """out_of_network_limit defaults to 50."""
        from prism.rag.config import RankingConfig

        config = RankingConfig()
        assert config.out_of_network_limit == 50

    def test_in_network_limit_accepts_valid_values(self):
        """in_network_limit accepts values >= 1."""
        from prism.rag.config import RankingConfig

        config_min = RankingConfig(in_network_limit=1)
        config_large = RankingConfig(in_network_limit=500)

        assert config_min.in_network_limit == 1
        assert config_large.in_network_limit == 500

    def test_out_of_network_limit_accepts_valid_values(self):
        """out_of_network_limit accepts values >= 1."""
        from prism.rag.config import RankingConfig

        config_min = RankingConfig(out_of_network_limit=1)
        config_large = RankingConfig(out_of_network_limit=500)

        assert config_min.out_of_network_limit == 1
        assert config_large.out_of_network_limit == 500

    def test_in_network_limit_rejects_zero(self):
        """in_network_limit rejects 0."""
        from prism.rag.config import RankingConfig

        with pytest.raises(ValidationError) as exc_info:
            RankingConfig(in_network_limit=0)

        assert "in_network_limit" in str(exc_info.value)

    def test_out_of_network_limit_rejects_zero(self):
        """out_of_network_limit rejects 0."""
        from prism.rag.config import RankingConfig

        with pytest.raises(ValidationError) as exc_info:
            RankingConfig(out_of_network_limit=0)

        assert "out_of_network_limit" in str(exc_info.value)

    def test_in_network_limit_rejects_negative(self):
        """in_network_limit rejects negative values."""
        from prism.rag.config import RankingConfig

        with pytest.raises(ValidationError) as exc_info:
            RankingConfig(in_network_limit=-1)

        assert "in_network_limit" in str(exc_info.value)

    def test_out_of_network_limit_rejects_negative(self):
        """out_of_network_limit rejects negative values."""
        from prism.rag.config import RankingConfig

        with pytest.raises(ValidationError) as exc_info:
            RankingConfig(out_of_network_limit=-1)

        assert "out_of_network_limit" in str(exc_info.value)


class TestRankingConfigYAMLIntegration:
    """Tests for RankingConfig YAML integration (T025-T028)."""

    def test_rag_config_has_ranking_field(self):
        """RAGConfig should have a ranking field of type RankingConfig (T025)."""
        from prism.rag.config import RAGConfig, RankingConfig

        config = RAGConfig()

        assert hasattr(config, "ranking")
        assert isinstance(config.ranking, RankingConfig)

    def test_rag_config_ranking_defaults(self):
        """RAGConfig ranking field has default RankingConfig values."""
        from prism.rag.config import RAGConfig

        config = RAGConfig()

        assert config.ranking.mode == "preference"
        assert config.ranking.out_of_network_scale == 0.75
        assert config.ranking.reply_scale == 0.75
        assert config.ranking.author_diversity_decay == 0.5
        assert config.ranking.author_diversity_floor == 0.25
        assert config.ranking.in_network_limit == 50
        assert config.ranking.out_of_network_limit == 50

    def test_rag_config_custom_ranking(self):
        """RAGConfig accepts custom ranking configuration."""
        from prism.rag.config import RAGConfig, RankingConfig

        config = RAGConfig(
            ranking=RankingConfig(
                mode="x_algo",
                out_of_network_scale=0.6,
                reply_scale=0.8,
            )
        )

        assert config.ranking.mode == "x_algo"
        assert config.ranking.out_of_network_scale == 0.6
        assert config.ranking.reply_scale == 0.8

    def test_load_config_with_ranking_section(self):
        """load_config loads ranking section from YAML (T025)."""
        import tempfile
        from pathlib import Path

        from prism.llm.config import load_config

        yaml_content = """
llm:
  provider: ollama
  model_id: mistral

rag:
  collection_name: test_posts
  ranking:
    mode: x_algo
    out_of_network_scale: 0.65
    reply_scale: 0.7
    author_diversity_decay: 0.6
    author_diversity_floor: 0.2
    in_network_limit: 100
    out_of_network_limit: 75
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = Path(f.name)

        try:
            config = load_config(temp_path)

            assert config.rag.ranking.mode == "x_algo"
            assert config.rag.ranking.out_of_network_scale == 0.65
            assert config.rag.ranking.reply_scale == 0.7
            assert config.rag.ranking.author_diversity_decay == 0.6
            assert config.rag.ranking.author_diversity_floor == 0.2
            assert config.rag.ranking.in_network_limit == 100
            assert config.rag.ranking.out_of_network_limit == 75
        finally:
            temp_path.unlink()

    def test_load_config_missing_ranking_uses_defaults(self):
        """load_config uses defaults when ranking section missing (T027)."""
        import tempfile
        from pathlib import Path

        from prism.llm.config import load_config

        yaml_content = """
llm:
  provider: ollama

rag:
  collection_name: posts
  feed_size: 10
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = Path(f.name)

        try:
            config = load_config(temp_path)

            # Should have default RankingConfig values
            assert config.rag.ranking.mode == "preference"
            assert config.rag.ranking.out_of_network_scale == 0.75
            assert config.rag.ranking.in_network_limit == 50
        finally:
            temp_path.unlink()
