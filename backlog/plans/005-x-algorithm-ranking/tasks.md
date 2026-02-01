# X Algorithm Ranking Tasks (TDD)

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
| Researcher configures ranking | FR-4 | RankingConfig tests |
| Operator sees INN/OON split | FR-1, FR-5 | Social graph, candidate sourcing tests |
| Analyst has diversity controls | FR-3 | Author diversity tests |

## Dependencies

```
Phase 1 (Data Model)
    │
    ├──► Phase 2 (Configuration)
    │         │
    │         └──► Phase 4 (Ranker Core)
    │                   │
    └──► Phase 3 (Social Graph) ──► Phase 4
                                      │
                                      └──► Phase 5 (Integration)
```

## Phase 1: Data Model Extensions ✅

### Post Model

- [x] T001 [TEST] Write test for Post.parent_id field existence and None default
- [x] T002 [IMPL] Add parent_id: str | None = None field to Post model
- [x] T003 [TEST] Write test for Post.to_metadata() including parent_id
- [x] T004 [IMPL] Update to_metadata() to include parent_id
- [x] T005 [TEST] Write test for Post.from_chroma_result() handling parent_id
- [x] T006 [IMPL] Update from_chroma_result() to handle parent_id from metadata

### SocialAgent Extension

- [x] T007 [TEST] Write test for SocialAgent.__init__ accepting following parameter
- [x] T008 [IMPL] Add following: set[str] = None parameter with default set()
- [x] T009 [TEST] Write test that SocialAgent rejects self-follow (agent_id in following)
- [x] T010 [IMPL] Add validation to prevent self-follow

## Phase 2: Configuration ✅

### RankingConfig Model

- [x] T011 [TEST] Write test for RankingConfig with mode field accepting x_algo/preference/random
- [x] T012 [IMPL] Create RankingConfig class with mode: Literal field
- [x] T013 [TEST] Write test for out_of_network_scale with default 0.75 and [0,1] validation
- [x] T014 [IMPL] Add out_of_network_scale field with Field validation
- [x] T015 [TEST] Write test for reply_scale with default 0.75 and [0,1] validation
- [x] T016 [IMPL] Add reply_scale field with Field validation
- [x] T017 [TEST] Write test for author_diversity_decay with default 0.5 and [0,1] validation
- [x] T018 [IMPL] Add author_diversity_decay field with Field validation
- [x] T019 [TEST] Write test for author_diversity_floor with default 0.25 and [0,1] validation
- [x] T020 [IMPL] Add author_diversity_floor field with Field validation
- [x] T021 [TEST] Write test that floor > decay raises ValidationError
- [x] T022 [IMPL] Add model_validator for floor <= decay constraint
- [x] T023 [TEST] Write test for in_network_limit and out_of_network_limit fields
- [x] T024 [IMPL] Add limit fields with ge=1 validation

### YAML Integration

- [x] T025 [TEST] Write test for loading RankingConfig from YAML
- [x] T026 [IMPL] Integrate RankingConfig into RAGConfig or config loader
- [x] T027 [TEST] Write test that missing ranking section uses defaults
- [x] T028 [IMPL] Ensure backward compatibility with existing configs

## Phase 3: Social Graph

### Protocol Definition

- [ ] T029 [TEST] Write test that SocialGraphProtocol is importable with required methods
- [ ] T030 [IMPL] Define SocialGraphProtocol in protocols.py

### Simple Implementation

- [ ] T031 [TEST] Write test for SimpleSocialGraph.get_following returns correct set
- [ ] T032 [IMPL] Implement SimpleSocialGraph with following dict
- [ ] T033 [TEST] Write test for SimpleSocialGraph.is_following returns correct bool
- [ ] T034 [IMPL] Add is_following method
- [ ] T035 [TEST] Write test for SimpleSocialGraph.get_followers (reverse lookup)
- [ ] T036 [IMPL] Build reverse index in __init__, implement get_followers
- [ ] T037 [TEST] Write test for empty following set returns empty set
- [ ] T038 [IMPL] Handle edge cases (missing agent, empty following)

## Phase 4: Ranker Core

### FeedRetriever Extension

- [ ] T039 [TEST] Write test for FeedRetriever.query_with_scores returning (Post, float) tuples
- [ ] T040 [IMPL] Add query_with_scores method including distances
- [ ] T041 [TEST] Write test that distance is converted to similarity correctly
- [ ] T042 [IMPL] Convert cosine distance [0,2] to similarity [0,1]

### XAlgorithmRanker Creation

- [ ] T043 [TEST] Write test for XAlgorithmRanker.__init__ with retriever and config
- [ ] T044 [IMPL] Create XAlgorithmRanker class with __init__
- [ ] T045 [TEST] Write test for get_feed signature accepting agent and social_graph
- [ ] T046 [IMPL] Add get_feed method stub

### Candidate Sourcing

- [ ] T047 [TEST] Write test for _get_in_network_candidates filtering by following
- [ ] T048 [IMPL] Implement in-network candidate retrieval with author_id filter
- [ ] T049 [TEST] Write test for _get_out_of_network_candidates excluding following
- [ ] T050 [IMPL] Implement OON candidate retrieval with similarity and exclusion

### Heuristic Rescoring

- [ ] T051 [TEST] Write test that OON posts receive out_of_network_scale multiplier
- [ ] T052 [IMPL] Apply OON scale factor in rescoring
- [ ] T053 [TEST] Write test that reply posts receive reply_scale multiplier
- [ ] T054 [IMPL] Apply reply scale factor based on parent_id
- [ ] T055 [TEST] Write test that scale factors multiply (not add)
- [ ] T056 [IMPL] Ensure multiplicative application of all factors

### Author Diversity

- [ ] T057 [TEST] Write test that first occurrence of author has no penalty
- [ ] T058 [IMPL] Initialize author_counts dict in rescoring
- [ ] T059 [TEST] Write test that second occurrence gets decay^1 penalty
- [ ] T060 [IMPL] Apply decay based on occurrence count
- [ ] T061 [TEST] Write test that floor prevents score below minimum
- [ ] T062 [IMPL] Use max(floor, decay^n) in calculation
- [ ] T063 [TEST] Write test that author counts reset per get_feed call
- [ ] T064 [IMPL] Initialize fresh author_counts in each get_feed

### Mode Delegation

- [ ] T065 [TEST] Write test that mode=preference delegates to retriever
- [ ] T066 [IMPL] Check mode and delegate for preference
- [ ] T067 [TEST] Write test that mode=random delegates to retriever
- [ ] T068 [IMPL] Check mode and delegate for random
- [ ] T069 [TEST] Write test that mode=x_algo runs full pipeline
- [ ] T070 [IMPL] Run full ranking for x_algo mode

### Sorting and Limiting

- [ ] T071 [TEST] Write test that candidates are sorted by final_score descending
- [ ] T072 [IMPL] Sort candidates before returning
- [ ] T073 [TEST] Write test that result is limited to feed_size
- [ ] T074 [IMPL] Slice to feed_size after sorting

## Phase 5: Integration

### Executor Update

- [ ] T075 [TEST] Write test for updated FeedRetrievalExecutor using ranker
- [ ] T076 [IMPL] Update executor to use XAlgorithmRanker when configured
- [ ] T077 [TEST] Write test for executor falling back to retriever for non-x_algo
- [ ] T078 [IMPL] Add mode check in executor

### Config Update

- [ ] T079 [TEST] Write test for default.yaml with ranking section
- [ ] T080 [IMPL] Add ranking section to default.yaml

### Integration Test

- [ ] T081 [TEST] Write integration test with 5 agents, follows, verify INN/OON ranking
- [ ] T082 [IMPL] Fix any issues found in integration

## Task Summary

| Phase | Tasks | [TEST] | [IMPL] |
|-------|-------|--------|--------|
| Phase 1: Data Model | T001-T010 | 5 | 5 |
| Phase 2: Configuration | T011-T028 | 9 | 9 |
| Phase 3: Social Graph | T029-T038 | 5 | 5 |
| Phase 4: Ranker Core | T039-T074 | 18 | 18 |
| Phase 5: Integration | T075-T082 | 4 | 4 |
| **Total** | **82** | **41** | **41** |

## Final Validation

After all implementation phases are complete:

- [ ] `uv run ruff check .` passes
- [ ] `uv run flake8 .` passes
- [ ] `uv run black --check .` passes
- [ ] `uv run pytest` passes (excluding integration)
- [ ] `uv run pytest -m integration` passes (with Ollama)
- [ ] Run spec tests with `/spec-tests` skill using `specs/tests/005-x-algorithm-ranking.md`
- [ ] All spec tests pass → feature complete
