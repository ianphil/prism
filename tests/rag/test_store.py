"""Tests for RAG store (ChromaDB collection factory)."""

import tempfile
from pathlib import Path

import chromadb

from prism.rag.config import RAGConfig
from prism.rag.store import _clients, clear_client_cache


class TestClearClientCache:
    """Tests for clear_client_cache() function."""

    def test_clears_client_cache(self):
        """clear_client_cache removes all cached clients."""
        from prism.rag.store import create_collection

        # Create a collection to populate the cache
        config = RAGConfig(collection_name="cache_test")
        create_collection(config)

        # Cache should have at least one entry
        assert len(_clients) > 0

        # Clear the cache
        clear_client_cache()

        # Cache should be empty
        assert len(_clients) == 0

    def test_clear_empty_cache_is_safe(self):
        """clear_client_cache is safe to call on empty cache."""
        clear_client_cache()  # Ensure empty
        clear_client_cache()  # Should not raise
        assert len(_clients) == 0


class TestCreateCollection:
    """Tests for create_collection() factory function."""

    def test_returns_chromadb_collection(self):
        """create_collection returns a chromadb.Collection."""
        from prism.rag.store import create_collection

        config = RAGConfig()
        collection = create_collection(config)

        assert isinstance(collection, chromadb.Collection)

    def test_in_memory_when_persist_directory_none(self):
        """Collection is in-memory when persist_directory is None."""
        from prism.rag.store import create_collection

        config = RAGConfig(persist_directory=None)
        collection = create_collection(config)

        # In-memory collections work but don't create files
        assert collection is not None
        # Can add and query without persistence
        collection.add(ids=["test"], documents=["test doc"])
        assert collection.count() == 1

    def test_persistent_when_persist_directory_set(self):
        """Collection is persistent when persist_directory is a path."""
        from prism.rag.store import create_collection

        with tempfile.TemporaryDirectory() as tmpdir:
            config = RAGConfig(persist_directory=tmpdir)
            collection = create_collection(config)

            # Add a document
            collection.add(ids=["test"], documents=["test doc"])
            assert collection.count() == 1

            # Verify persistence directory contains data
            persist_path = Path(tmpdir)
            assert persist_path.exists()
            # ChromaDB creates files in the directory
            assert any(persist_path.iterdir())

    def test_uses_configured_collection_name(self):
        """Collection uses the name from config."""
        from prism.rag.store import create_collection

        config = RAGConfig(collection_name="my_custom_posts")
        collection = create_collection(config)

        assert collection.name == "my_custom_posts"

    def test_configures_embedding_function(self):
        """Collection has an embedding function configured."""
        from prism.rag.store import create_collection

        config = RAGConfig(embedding_model="all-MiniLM-L6-v2")
        collection = create_collection(config)

        # Verify embedding function is set by adding docs and querying
        collection.add(ids=["1"], documents=["Hello world"])
        results = collection.query(query_texts=["greeting"], n_results=1)

        # Query should work (meaning embeddings are being generated)
        assert "ids" in results
        assert len(results["ids"]) == 1

    def test_get_or_create_semantics(self):
        """Calling create_collection twice returns the same collection."""
        from prism.rag.store import create_collection

        config = RAGConfig(collection_name="test_collection")

        collection1 = create_collection(config)
        collection1.add(ids=["1"], documents=["doc1"])

        # Create again with same config
        collection2 = create_collection(config)

        # Should see the same data (get_or_create semantics)
        assert collection2.count() == 1
