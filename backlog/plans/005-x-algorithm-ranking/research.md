# X Algorithm Ranking Conformance Research

**Date**: 2026-02-01
**Spec Version Reviewed**: [twitter/the-algorithm](https://github.com/twitter/the-algorithm) (cloned 2026-01-31)
**Plan Version**: plan.md

## Summary

This feature implements a simplified version of X's recommendation algorithm focused on the heuristic rescoring layer. The documented scale factors from `RescoringFactorProvider.scala` are directly applicable. The ML-based ranking stages are approximated with embedding similarity, which is an acceptable trade-off for simulation purposes.

## Conformance Analysis

### 1. Out-of-Network Scale Factor

| Aspect | Plan | Spec | Status |
|--------|------|------|--------|
| Default value | 0.75 | 0.75 | CONFORMANT |
| Application | Multiplicative | Multiplicative | CONFORMANT |
| Scope | All OON posts | OON posts | CONFORMANT |

**Source**: `ScoredTweetsParam.scala` - `OutOfNetworkScaleFactor`

### 2. Reply Scale Factor

| Aspect | Plan | Spec | Status |
|--------|------|------|--------|
| Default value | 0.75 | 0.75 | CONFORMANT |
| Detection | `parent_id is not None` | `isReply` flag | CONFORMANT |

**Source**: `ScoredTweetsParam.scala` - `ReplyScaleFactor`

### 3. Author Diversity

| Aspect | Plan | Spec | Status |
|--------|------|------|--------|
| Decay factor | 0.5 | 0.5 | CONFORMANT |
| Floor | 0.25 | 0.25 | CONFORMANT |
| Reset | Per feed request | Per ranking pass | CONFORMANT |
| Formula | `max(floor, decay^n)` | `max(floor, decay^n)` | CONFORMANT |

**Source**: `RescoringFactorProvider.scala` - `AuthorDiversityDecayFactor`, `AuthorDiversityFloor`

### 4. Candidate Sourcing

| Aspect | Plan | Spec | Status |
|--------|------|------|--------|
| In-network source | Follow graph | Earlybird (follow graph) | SIMPLIFIED |
| OON source | RAG similarity | UTEG, SimClusters, FRS | SIMPLIFIED |
| Default limits | 50/50 | 600 INN, 800 OON | SCALED DOWN |

**Recommendation**: The plan simplifies candidate sourcing to two sources (follow graph + RAG). This is acceptable for simulation but should be documented as a simplification.

### 5. Base Score Computation

| Aspect | Plan | Spec | Status |
|--------|------|------|--------|
| Method | Embedding similarity | ML heavy ranker | APPROXIMATION |
| Score range | 0.0-1.0 (similarity) | Model output | DIFFERENT |

**Recommendation**: Embedding similarity is a reasonable approximation for simulation. The actual X algorithm uses neural network scores trained on engagement labels. Document this as an intentional simplification.

### 6. User Feedback Factors

| Aspect | Plan | Spec | Status |
|--------|------|------|--------|
| Show less | Not implemented | 0.05x | NOT IMPLEMENTED |
| Show more | Not implemented | 20.0x | NOT IMPLEMENTED |

**Recommendation**: User feedback factors are out of scope for MVP. Could be added in future if agent memory tracks explicit feedback.

### 7. Media/Live Content Boost

| Aspect | Plan | Spec | Status |
|--------|------|------|--------|
| Media boost | Not implemented | Learned in ML | NOT IMPLEMENTED |
| Live content | Not implemented | 1.0x (max 10000) | NOT IMPLEMENTED |

**Note**: Per the research, media effects are learned by ML models through features, not explicit boost multipliers in the heuristic layer.

## New Features in Spec (Not in Plan)

The following X algorithm features are documented but not planned for implementation:

1. **MTL Normalization** - Multi-task learning calibration based on author followers
2. **Candidate Source Diversity** - Decay for repeat candidate sources (0.9 decay, 0.8 floor)
3. **Real Graph Scores** - Relationship strength between users
4. **Safety Filtering** - Offensive/spam content suppression
5. **Engagement Recency** - Time-weighted engagement signals

All of these are acceptable omissions for MVP as they add complexity without fundamentally changing the ranking behavior for simulation purposes.

## Recommendations

### Critical Updates

None required. The core scale factors are correctly documented and planned.

### Minor Updates

1. **Document approximations** - Add a note in plan.md that embedding similarity approximates ML ranking
2. **Clarify candidate limits** - Note that 50/50 is scaled down from X's 600/800 for simulation scale

### Future Enhancements

1. **User feedback** - Add "show more"/"show less" if agent memory supports explicit feedback
2. **Engagement velocity** - Weight by recency of engagement
3. **Source diversity** - Track and decay repeat candidate sources
4. **Media features** - Boost posts with images/video based on research

## Sources

- [X Algorithm GitHub Repository](https://github.com/twitter/the-algorithm)
- `home-mixer/server/src/main/scala/com/twitter/home_mixer/product/scored_tweets/param/ScoredTweetsParam.scala`
- `home-mixer/server/src/main/scala/com/twitter/home_mixer/product/scored_tweets/scorer/RescoringFactorProvider.scala`
- Local research notes: `aidocs/x-algorithm-research.md`

## Conclusion

The plan is **CONFORMANT** with X's documented heuristic rescoring layer. The core scale factors (OON 0.75, reply 0.75, author diversity 0.5/0.25) match exactly. The use of embedding similarity as a base score is a documented approximation of the ML heavy ranker. The simplified candidate sourcing (follow graph + RAG) is an acceptable adaptation for simulation scale.

No blocking issues identified. Proceed with implementation.
