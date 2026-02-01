# Work Plan: 005-x-algorithm-ranking

## Status: Phase 1 Complete

| Phase | Status | Tasks |
|-------|--------|-------|
| Phase 1: Data Model | ✅ Complete | T001-T010 |
| Phase 2: Configuration | Pending | T011-T028 |
| Phase 3: Social Graph | Pending | T029-T038 |
| Phase 4: Ranker Core | Pending | T039-T074 |
| Phase 5: Integration | Pending | T075-T082 |

## Current Focus

Ready to begin Phase 2 (Configuration).

## Phase Summary

### Phase 1: Data Model (10 tasks)
- Add `parent_id` field to `Post` for reply detection
- Add `following` field to `SocialAgent` for in-network classification
- Validation to prevent self-follow

### Phase 2: Configuration (18 tasks)
- Create `RankingConfig` Pydantic model
- All X algorithm scale factors with defaults
- YAML integration and backward compatibility

### Phase 3: Social Graph (10 tasks)
- Define `SocialGraphProtocol`
- Implement `SimpleSocialGraph` with forward/reverse lookups

### Phase 4: Ranker Core (36 tasks)
- Extend `FeedRetriever` with score access
- Create `XAlgorithmRanker` class
- Implement candidate sourcing (INN/OON)
- Implement heuristic rescoring
- Implement author diversity
- Mode delegation

### Phase 5: Integration (8 tasks)
- Update `FeedRetrievalExecutor`
- Update `default.yaml`
- Integration test

## Next Actions

1. Start Phase 1: `uv run pytest tests/rag/test_models.py -v`
2. Implement T001-T010 following TDD
3. Proceed to Phase 2 after Phase 1 tests pass

## Commands

```bash
# Run tests for current phase
uv run pytest tests/rag/test_models.py tests/agents/test_social_agent.py -v

# Run all tests
uv run pytest

# Run linting
uv run ruff check . && uv run flake8 . && uv run black --check .
```
