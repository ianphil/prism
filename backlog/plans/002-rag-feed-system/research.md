# RAG Feed System Conformance Research

**Date**: 2026-01-29
**Spec Version Reviewed**: [ChromaDB 0.4.x](https://docs.trychroma.com/) | [Ollama Embeddings API](https://github.com/ollama/ollama/blob/main/docs/api.md#generate-embeddings)
**Plan Version**: plan.md (draft)

## Summary

The plan conforms well to ChromaDB's Python API and Ollama's embedding capabilities. Minor adjustments needed for embedding function configuration and metadata handling. The sentence-transformers fallback is straightforward.

## Conformance Analysis

### 1. ChromaDB Collection API

| Aspect | Plan | Spec | Status |
|--------|------|------|--------|
| Collection creation | `client.get_or_create_collection()` | ✅ Supported | CONFORMANT |
| Embedding function | Pass to collection constructor | `embedding_function` param | CONFORMANT |
| Metadata storage | Store Post fields as metadata | Supports dict metadata | CONFORMANT |
| Query by embedding | `collection.query(query_embeddings=...)` | ✅ Supported | CONFORMANT |
| Random sampling | Custom implementation needed | No native random sample | UPDATE NEEDED |

**Recommendation**: ChromaDB doesn't have native random sampling. For random mode:
- Option A: Retrieve all IDs, sample in Python, then `collection.get(ids=sampled_ids)`
- Option B: Store a `random_key` metadata field and query by range (less clean)
- **Chosen**: Option A — simpler, acceptable for corpus sizes < 100K

### 2. Ollama Embeddings

| Aspect | Plan | Spec | Status |
|--------|------|------|--------|
| Model | `nomic-embed-text` | Available via `ollama pull nomic-embed-text` | CONFORMANT |
| API | `/api/embeddings` endpoint | POST with model + prompt | CONFORMANT |
| Integration | Custom EmbeddingFunction for ChromaDB | ChromaDB supports custom functions | CONFORMANT |
| Batch embedding | Embed multiple texts | Ollama supports single text per call | UPDATE NEEDED |

**Recommendation**: Ollama embedding API processes one text at a time. For batch insertion:
- Loop over texts with individual API calls, or
- Use sentence-transformers for batch embedding (faster)
- Default to sentence-transformers for performance; Ollama optional

### 3. ChromaDB Embedding Functions

| Aspect | Plan | Spec | Status |
|--------|------|------|--------|
| Built-in functions | `chromadb.utils.embedding_functions` | Includes SentenceTransformerEmbeddingFunction | CONFORMANT |
| Custom function | Implement `EmbeddingFunction` protocol | `__call__(self, input: Documents) -> Embeddings` | CONFORMANT |
| Default | sentence-transformers `all-MiniLM-L6-v2` | Fast, good quality | CONFORMANT |

**Recommendation**: Use ChromaDB's built-in `SentenceTransformerEmbeddingFunction` as default. Create custom `OllamaEmbeddingFunction` for users who want Ollama-only setup.

### 4. Post Metadata

| Aspect | Plan | Spec | Status |
|--------|------|------|--------|
| Supported types | str, int, float, bool | ChromaDB metadata supports these | CONFORMANT |
| datetime storage | Store as ISO string or timestamp | ChromaDB doesn't support datetime directly | UPDATE NEEDED |
| Filtering | `where={"has_media": True}` | ✅ Supported | CONFORMANT |

**Recommendation**: Store `timestamp` as ISO 8601 string (`timestamp.isoformat()`) for filtering, or as float (`timestamp.timestamp()`) for range queries. ISO string is more readable.

### 5. ChromaDB Persistence

| Aspect | Plan | Spec | Status |
|--------|------|------|--------|
| In-memory | `chromadb.Client()` | ✅ Default ephemeral | CONFORMANT |
| Persistent | `chromadb.PersistentClient(path=...)` | ✅ Supported | CONFORMANT |
| Settings | Via client constructor | `chromadb.Settings(...)` for advanced | CONFORMANT |

**Recommendation**: Plan's config-driven approach (null = in-memory, path = persistent) aligns with ChromaDB API.

## New Features in Spec (Not in Plan)

1. **ChromaDB 0.4+ async support**: `chromadb.AsyncHttpClient` for async operations
   - Not critical for MVP; sync client wrapped in executor is sufficient

2. **Metadata indexing**: ChromaDB allows indexing specific metadata fields
   - Future optimization; not needed for MVP corpus sizes

3. **Distance metrics**: ChromaDB supports `cosine`, `l2`, `ip` distance functions
   - Plan assumes cosine (default); conformant

## Recommendations

### Critical Updates

1. **Random sampling implementation**
   - ChromaDB lacks native random sample
   - Implement: `collection.get()` all IDs → Python `random.sample()` → `collection.get(ids=...)`
   - Document performance implication for large corpora (>50K posts)

2. **Batch embedding strategy**
   - Ollama embeddings are single-text; slow for batch insertion
   - Default to `SentenceTransformerEmbeddingFunction` for performance
   - Ollama embedding optional via config `embedding_provider: ollama | sentence-transformers`

### Minor Updates

3. **Timestamp storage format**
   - Store as ISO 8601 string for human readability
   - Add utility functions: `timestamp_to_meta()`, `meta_to_timestamp()`

4. **Collection metadata schema documentation**
   - Document which Post fields become metadata vs document text
   - `documents`: Post.text (for embedding)
   - `metadatas`: all other fields (for filtering and retrieval)

### Future Enhancements

5. **Async ChromaDB client**
   - When simulation requires concurrent feed retrievals, migrate to `AsyncHttpClient`
   - Current sync wrapper sufficient for single-threaded MVP

6. **Embedding model selection**
   - Add config option for embedding model name
   - `all-MiniLM-L6-v2` (fast), `all-mpnet-base-v2` (accurate), or Ollama models

## Sources

- [ChromaDB Python Docs](https://docs.trychroma.com/getting-started)
- [ChromaDB Embedding Functions](https://docs.trychroma.com/guides/embeddings)
- [Ollama Embeddings API](https://github.com/ollama/ollama/blob/main/docs/api.md#generate-embeddings)
- [Sentence Transformers](https://www.sbert.net/)

## Conclusion

The plan is largely conformant with ChromaDB and Ollama specifications. Key updates:

1. Implement Python-side random sampling (ChromaDB limitation)
2. Default to sentence-transformers for batch embedding performance
3. Store timestamps as ISO strings in metadata

No blocking issues. Implementation can proceed with minor adjustments documented above.
