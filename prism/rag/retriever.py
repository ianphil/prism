"""Feed retrieval from ChromaDB for the RAG feed system."""

import random
from typing import Literal

import chromadb

from prism.rag.models import Post


class FeedRetriever:
    """Retrieves feeds from ChromaDB based on agent interests or random sampling."""

    def __init__(
        self,
        collection: chromadb.Collection,
        feed_size: int = 5,
        default_mode: Literal["preference", "random"] = "preference",
    ) -> None:
        """Initialize with a ChromaDB collection.

        Args:
            collection: ChromaDB collection with embedding function configured.
            feed_size: Number of posts to return per feed (1-20).
            default_mode: Default retrieval mode if not specified in get_feed().
        """
        self._collection = collection
        self._feed_size = feed_size
        self._default_mode = default_mode

    def add_post(self, post: Post) -> None:
        """Index a single post in the collection.

        Args:
            post: Post to index.
        """
        self._collection.upsert(
            ids=[post.id],
            documents=[post.text],
            metadatas=[post.to_metadata()],
        )

    def add_posts(self, posts: list[Post]) -> None:
        """Index multiple posts in the collection.

        Args:
            posts: List of posts to index.
        """
        if not posts:
            return

        self._collection.upsert(
            ids=[p.id for p in posts],
            documents=[p.text for p in posts],
            metadatas=[p.to_metadata() for p in posts],
        )

    def get_feed(
        self,
        interests: list[str] | None = None,
        mode: Literal["preference", "random"] | None = None,
    ) -> list[Post]:
        """Retrieve a feed of posts.

        Args:
            interests: Agent interests for preference mode.
                Required if mode="preference".
            mode: Retrieval mode. Uses default_mode if None.

        Returns:
            List of Post objects (up to feed_size).

        Raises:
            ValueError: If mode="preference" and interests is None or empty.
            RuntimeError: If collection is empty.
        """
        effective_mode = mode if mode is not None else self._default_mode

        # Check for empty collection
        if self.count() == 0:
            raise RuntimeError("Collection is empty")

        if effective_mode == "preference":
            return self._get_feed_preference(interests)
        else:
            return self._get_feed_random()

    def _get_feed_preference(self, interests: list[str] | None) -> list[Post]:
        """Retrieve feed using preference mode (similarity to interests).

        Args:
            interests: List of interest strings to query by.

        Returns:
            List of Post objects ranked by similarity.

        Raises:
            ValueError: If interests is None or empty.
        """
        if not interests:
            raise ValueError("interests required for preference mode")

        query_text = " ".join(interests)
        results = self._collection.query(
            query_texts=[query_text],
            n_results=self._feed_size,
            include=["documents", "metadatas"],
        )

        return self._results_to_posts(results)

    def _get_feed_random(self) -> list[Post]:
        """Retrieve feed using random sampling.

        Note:
            This method has O(n) complexity where n is the collection size,
            as it fetches all document IDs before sampling. Suitable for
            collections under 100K posts.

        Returns:
            List of randomly sampled Post objects.
        """
        all_data = self._collection.get()
        all_ids = all_data["ids"]

        sample_size = min(self._feed_size, len(all_ids))
        sampled_ids = random.sample(all_ids, sample_size)

        results = self._collection.get(
            ids=sampled_ids,
            include=["documents", "metadatas"],
        )

        return self._results_to_posts_get(results)

    def _results_to_posts(self, results: dict) -> list[Post]:
        """Convert ChromaDB query results to Post objects.

        Args:
            results: ChromaDB query results dict with ids, documents, metadatas.

        Returns:
            List of Post objects.
        """
        posts = []
        # Query results have nested lists (one per query)
        ids = results["ids"][0]
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]

        for id_, doc, meta in zip(ids, documents, metadatas):
            posts.append(Post.from_chroma_result(id_, doc, meta))

        return posts

    def _results_to_posts_get(self, results: dict) -> list[Post]:
        """Convert ChromaDB get results to Post objects.

        Args:
            results: ChromaDB get results dict with ids, documents, metadatas.

        Returns:
            List of Post objects.
        """
        posts = []
        # Get results have flat lists
        ids = results["ids"]
        documents = results["documents"]
        metadatas = results["metadatas"]

        for id_, doc, meta in zip(ids, documents, metadatas):
            posts.append(Post.from_chroma_result(id_, doc, meta))

        return posts

    def count(self) -> int:
        """Return the number of indexed posts."""
        return self._collection.count()

    def clear(self) -> None:
        """Remove all posts from the collection."""
        all_ids = self._collection.get()["ids"]
        if all_ids:
            self._collection.delete(ids=all_ids)
