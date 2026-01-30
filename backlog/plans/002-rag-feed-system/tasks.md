# RAG Feed System Tasks (TDD)

## TDD Approach

All implementation follows strict Red-Green-Refactor:
1. **RED**: Write failing test first
2. **GREEN**: Write minimal code to pass test
3. **REFACTOR**: Clean up while keeping tests green

### Two Test Layers

| Layer | Purpose | When to Run |
|-------|---------|-------------|
| **Unit Tests** | Implementation TDD (Red-Green-Refactor) | During implementation |
| **Spec Tests** | Intent-based acceptance validation | After all phases complete |

## User Story Mapping

| Story | spec.md Reference | Spec Tests |
|-------|-------------------|------------|
| Researcher receives personalized feeds | FR-5 (Feed Retrieval) | FeedRetriever supports preference-based retrieval |
| Experimenter switches feed modes | FR-2 (RAG Configuration), FR-5.3 | FeedRetriever supports random sampling mode |
| Developer stores posts with media | FR-1 (Post Data Model), FR-4 (Post Storage) | Post is validated Pydantic model, Post provides ChromaDB conversion |
| Agent sees formatted feed | FR-6 (Feed Rendering) | Feed formatter renders posts with media, engagement, timestamps |

## Dependencies

```
Phase 1 (Models + Config) ──► Phase 2 (ChromaDB) ──► Phase 3 (Retrieval)
                                                          │
                                                          ▼
                                                   Phase 4 (Formatting)
                                                          │
                                                          ▼
                                                   Phase 5 (Integration)
```

## Phase 1: Data Model and Configuration

### Post Model
- [x] T001 [TEST] Write tests for `Post` Pydantic model
  - Valid post with all fields
  - Default values for optional fields (has_media=False, likes=0, etc.)
  - Negative likes/reshares/replies raises validation error
  - Negative velocity raises validation error
  - media_type enum validation
- [x] T002 [IMPL] Implement `Post` in `prism/rag/models.py`
  - Pydantic BaseModel with all PRD-specified fields
  - Field constraints (ge=0 for metrics)
  - Literal type for media_type
- [x] T003 [TEST] Write tests for `Post.to_metadata()` and `Post.from_chroma_result()`
  - to_metadata returns dict with all fields
  - timestamp converted to ISO string
  - from_chroma_result reconstructs Post correctly
- [x] T004 [IMPL] Implement `to_metadata()` and `from_chroma_result()` methods

### RAG Configuration
- [x] T005 [TEST] Write tests for `RAGConfig` Pydantic model
  - Default values are correct
  - feed_size out of range (0 or 21) raises error
  - Invalid mode raises error
  - Valid config parses successfully
- [x] T006 [IMPL] Implement `RAGConfig` in `prism/rag/config.py`
- [x] T007 [IMPL] Extend `PrismConfig` to include `rag: RAGConfig`
  - Modify `prism/llm/config.py` to import and add RAGConfig
- [x] T008 [IMPL] Update `configs/default.yaml` with `rag:` section

## Phase 2: ChromaDB Integration

### Collection Factory
- [x] T009 [TEST] Write tests for `create_collection()`
  - Returns chromadb.Collection
  - In-memory when persist_directory is None
  - Persistent when persist_directory is set
  - Configures embedding function
- [x] T010 [IMPL] Implement `create_collection()` in `prism/rag/store.py`
  - chromadb.Client() for in-memory
  - chromadb.PersistentClient() for persistent
  - SentenceTransformerEmbeddingFunction as default

### Optional: Ollama Embeddings
- [x] T011 [TEST] Write tests for `OllamaEmbeddingFunction` (optional)
  - Implements chromadb embedding function protocol
  - Calls Ollama API for embedding
- [x] T012 [IMPL] Implement `OllamaEmbeddingFunction` in `prism/rag/embeddings.py`
  - Custom embedding function for Ollama users
  - Calls /api/embeddings endpoint

## Phase 3: Feed Retrieval

### FeedRetriever Class
- [x] T013 [TEST] Write tests for `FeedRetriever.__init__()`
  - Accepts collection and config
  - Stores feed_size and default_mode
- [x] T014 [TEST] Write tests for `FeedRetriever.add_post()`
  - Indexes single post in collection
  - Post metadata stored correctly
- [x] T015 [TEST] Write tests for `FeedRetriever.add_posts()`
  - Batch indexes multiple posts
  - All posts retrievable after indexing
- [x] T016 [IMPL] Implement `FeedRetriever` with `add_post()` and `add_posts()` in `prism/rag/retriever.py`

### Preference Mode Retrieval
- [x] T017 [TEST] Write tests for `get_feed(mode="preference")`
  - Returns list of Post objects
  - Relevant posts ranked higher (by interest similarity)
  - Respects feed_size limit
  - Raises error if interests is None/empty
- [x] T018 [IMPL] Implement preference mode in `get_feed()`

### Random Mode Retrieval
- [x] T019 [TEST] Write tests for `get_feed(mode="random")`
  - Returns list of Post objects
  - Does not require interests
  - Returns diverse posts (not always same order)
  - Respects feed_size limit
- [x] T020 [IMPL] Implement random mode in `get_feed()`

### Edge Cases
- [x] T021 [TEST] Write tests for edge cases
  - Empty collection raises RuntimeError
  - Fewer posts than feed_size returns all posts
  - count() returns correct number
  - clear() removes all posts
- [x] T022 [IMPL] Implement `count()` and `clear()` methods

## Phase 4: Feed Formatting

### Format Function
- [x] T023 [TEST] Write tests for `format_feed_for_prompt()`
  - Returns formatted string
  - Includes post text
  - Includes media indicator when has_media=True
  - Uses correct emoji for media_type (📷, 🎬, 🎞️)
  - Includes engagement stats (❤️, 🔁, 💬)
  - Includes relative timestamp
- [x] T024 [IMPL] Implement `format_feed_for_prompt()` in `prism/rag/formatting.py`

### Relative Timestamp
- [x] T025 [TEST] Write tests for relative timestamp formatting
  - Minutes ago (e.g., "5m ago")
  - Hours ago (e.g., "3h ago")
  - Days ago (e.g., "2d ago")
- [x] T026 [IMPL] Implement `format_relative_time()` helper function

## Phase 5: Integration

### Package Exports
- [ ] T027 [IMPL] Create `__init__.py` files with exports
  - `prism/rag/__init__.py`: Post, RAGConfig, FeedRetriever, format_feed_for_prompt
  - `tests/rag/__init__.py`

### Dependencies
- [ ] T028 [IMPL] Add runtime dependencies via `uv add`
  - `uv add chromadb`
  - `uv add sentence-transformers`

### Integration Test
- [ ] T029 [TEST] Write integration test (marked with `@pytest.mark.integration`)
  - Creates collection from config
  - Creates FeedRetriever
  - Indexes sample posts
  - Retrieves feed with preference mode
  - Retrieves feed with random mode
  - Formats feed for prompt
  - Verifies formatted output contains expected elements

### Spec Tests
- [ ] T030 [SPEC] Run spec tests using `specs/tests/002-rag-feed-system.md`

## Task Summary

| Phase | Tasks | [TEST] | [IMPL] | [SPEC] |
|-------|-------|--------|--------|--------|
| Phase 1: Models + Config | T001-T008 | 3 | 5 | 0 |
| Phase 2: ChromaDB | T009-T012 | 2 | 2 | 0 |
| Phase 3: Retrieval | T013-T022 | 6 | 4 | 0 |
| Phase 4: Formatting | T023-T026 | 2 | 2 | 0 |
| Phase 5: Integration | T027-T030 | 1 | 2 | 1 |
| **Total** | **30** | **14** | **15** | **1** |

## Final Validation

After all implementation phases are complete:

- [ ] `uv run ruff check .` passes
- [ ] `uv run flake8 .` passes
- [ ] `uv run black --check .` passes
- [ ] `uv run pytest` passes (all tests including new RAG tests)
- [ ] Run spec tests with `/spec-tests` skill using `specs/tests/002-rag-feed-system.md`
- [ ] All spec tests pass → feature complete
