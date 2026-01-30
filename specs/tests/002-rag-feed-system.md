---
target:
  - prism/rag/models.py
  - prism/rag/config.py
  - prism/rag/store.py
  - prism/rag/retriever.py
  - prism/rag/formatting.py
  - prism/llm/config.py
  - configs/default.yaml
---

# RAG Feed System Spec Tests

Validates that PRISM's RAG feed system provides config-driven ChromaDB integration, post storage with embeddings, preference and random feed retrieval modes, and formatted feed output for agent prompts.

## Post Data Model

### Post is a validated Pydantic model with PRD-specified fields

The simulation tracks post engagement, media presence, and velocity for the X algorithm. If the Post model lacks these fields, downstream ranking and cascade analysis break entirely.

```
Given the prism/rag/models.py file
When examining the Post class
Then it inherits from pydantic.BaseModel
And it has an "id" field typed as str
And it has an "author_id" field typed as str
And it has a "text" field typed as str
And it has a "timestamp" field typed as datetime
And it has a "has_media" field typed as bool with default False
And it has a "media_type" field typed as Literal["image", "video", "gif"] | None
And it has a "likes" field typed as int with default 0
And it has a "reshares" field typed as int with default 0
And it has a "replies" field typed as int with default 0
And it has a "velocity" field typed as float with default 0.0
```

### Post validates engagement metrics are non-negative

Negative engagement metrics (e.g., -5 likes) would corrupt cascade analysis and produce invalid virality calculations. Validation catches data corruption early.

```
Given the prism/rag/models.py file
When examining the Post class field definitions
Then the likes field has a constraint ge=0 (greater than or equal to 0)
And the reshares field has a constraint ge=0
And the replies field has a constraint ge=0
And the velocity field has a constraint ge=0.0
```

### Post provides ChromaDB conversion methods

Posts must serialize to ChromaDB metadata and reconstruct from query results. Without these methods, indexing and retrieval cannot work.

```
Given the prism/rag/models.py file
When examining the Post class
Then it has a to_metadata method that returns a dict
And it has a from_chroma_result classmethod that reconstructs a Post from ChromaDB data
```

## RAG Configuration

### RAGConfig provides validated configuration with sensible defaults

Researchers need to configure feed retrieval without editing code. Invalid config (e.g., feed_size=100) must be caught at startup, not during a simulation.

```
Given the prism/rag/config.py file
When examining the RAGConfig class
Then it inherits from pydantic.BaseModel
And it has a "collection_name" field with default "posts"
And it has a "embedding_model" field with a default value
And it has a "feed_size" field with constraints between 1 and 20
And it has a "mode" field typed as Literal["preference", "random"]
```

### PrismConfig includes RAG configuration section

The RAG system must be configurable through the same config loading mechanism as the LLM. A separate config file would fragment the experiment setup.

```
Given the prism/llm/config.py file
When examining the PrismConfig class
Then it has a "rag" field of type RAGConfig (imported from prism.rag.config)
And the rag field has a default value of RAGConfig()
```

### Default YAML includes RAG configuration

A missing RAG section in the default config would force every user to manually add it, breaking the zero-config first run experience.

```
Given the configs/default.yaml file
When examining its contents
Then it contains a "rag" section
And the rag section specifies "collection_name", "feed_size", and "mode" keys
```

## ChromaDB Integration

### Collection factory creates ChromaDB collection from config

The factory decouples retriever code from ChromaDB construction details. Without it, changing embedding providers would require modifying retriever code.

```
Given the prism/rag/store.py file
When examining the create_collection function
Then it accepts a RAGConfig parameter (or similar config object)
And it returns a chromadb Collection object
And it configures an embedding function based on the config
```

### Collection factory supports both in-memory and persistent storage

Development uses ephemeral storage for fast iteration; experiments need persistent storage for checkpointing. The factory must support both via config.

```
Given the prism/rag/store.py file
When examining the create_collection function implementation
Then it creates an in-memory client when persist_directory is None
And it creates a persistent client when persist_directory is a path string
```

## Feed Retrieval

### FeedRetriever provides post indexing methods

Posts must be indexed before retrieval. Without add_post/add_posts, there's no way to populate the feed system.

```
Given the prism/rag/retriever.py file
When examining the FeedRetriever class
Then it has an add_post method that accepts a Post object
And it has an add_posts method that accepts a list of Post objects
```

### FeedRetriever supports preference-based retrieval

The core value proposition is personalized feeds based on agent interests. If preference mode doesn't query by interest similarity, agents receive irrelevant content.

```
Given the prism/rag/retriever.py file
When examining the FeedRetriever class
Then it has a get_feed method
And the get_feed method accepts an interests parameter (list of strings)
And the get_feed method accepts a mode parameter
And preference mode uses the interests to query the collection by similarity
```

### FeedRetriever supports random sampling mode

Experiments need a control group with non-personalized feeds. Without random mode, researchers cannot isolate the effect of algorithmic curation.

```
Given the prism/rag/retriever.py file
When examining the get_feed method implementation
Then it supports mode="random"
And random mode samples posts without using interest similarity
And it returns a list of Post objects
```

### FeedRetriever respects feed_size configuration

The PRD specifies 5-10 posts per agent turn. Returning more overwhelms the context window; fewer starves agent decision-making.

```
Given the prism/rag/retriever.py file
When examining the FeedRetriever class
Then it has a feed_size parameter (in constructor or config)
And get_feed returns at most feed_size posts
```

## Feed Formatting

### Feed formatter renders posts with media indicators

Agents need to see visual content indicators to make realistic decisions about visual posts. Without formatting, the visual virality hypothesis cannot be tested.

```
Given the prism/rag/formatting.py file
When examining the format_feed_for_prompt function
Then it accepts a list of Post objects
And it returns a formatted string
And the output includes media indicators when has_media is True
And the output uses emoji format for media type (like 📷 for image)
```

### Feed formatter includes engagement statistics

Agents should consider post popularity when deciding to engage. Without visible engagement stats, agents cannot exhibit realistic bandwagon behavior.

```
Given the prism/rag/formatting.py file
When examining the format_feed_for_prompt function implementation
Then the output includes like counts
And the output includes reshare counts
And the output includes reply counts
And the stats use emoji format (like ❤️ for likes)
```

### Feed formatter includes relative timestamps

Recency affects engagement decisions. Showing "3h ago" vs "2 days ago" helps agents prioritize timely content.

```
Given the prism/rag/formatting.py file
When examining the format_feed_for_prompt function implementation
Then the output includes timestamp information for each post
And timestamps are formatted as relative time (e.g., "3h ago", "2d ago")
```
