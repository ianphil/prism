# RAG Feed System Contracts

Interface definitions for the RAG feed system.

## Contract Documents

| Contract | Purpose |
|----------|---------|
| [post.md](post.md) | Post model schema and validation rules |
| [retriever.md](retriever.md) | FeedRetriever interface specification |
| [config.md](config.md) | RAGConfig schema for YAML configuration |

## Contract Principles

- All contracts use Pydantic for validation
- Interfaces are async-compatible for future parallelism
- ChromaDB details are encapsulated behind FeedRetriever
- Configuration follows the existing PrismConfig pattern
