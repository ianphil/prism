# X Algorithm Ranking Contracts

Interface definitions for the X algorithm ranking feature.

## Contract Documents

| Contract | Purpose |
|----------|---------|
| [ranking-config.md](ranking-config.md) | Configuration schema for ranking parameters |
| [social-graph.md](social-graph.md) | Protocol for social graph queries |
| [ranker.md](ranker.md) | XAlgorithmRanker interface |

## Contract Principles

- All scale factors validated to [0.0, 1.0] range
- Ranker is stateless between calls (author tracking is per-call)
- Social graph access is read-only
- Configuration is immutable during simulation
