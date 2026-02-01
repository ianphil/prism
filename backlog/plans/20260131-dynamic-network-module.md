---
title: "Dynamic Network Module"
status: open
priority: medium
created: 2026-01-31
depends_on: ["20260127-experiment-framework.md"]
supports_studies: ["study-growth-strategies.md"]
---

# Dynamic Network Module

## Summary

Add dynamic follow graph capability where edges can be added during simulation based on a probabilistic follow decision model, enabling study of follower growth strategies.

## Motivation

Study 2 (growth strategies) requires networks that evolve as agents interact. The current design assumes static topology, but testing follower acquisition strategies requires agents to gain/lose followers based on their behavior. This unlocks research into how small accounts can grow their audience.

## Proposal

### Goals

- Enable follow edges to be added during simulation rounds
- Implement probabilistic follow decision model triggered by engagement
- Track follower changes per round for longitudinal analysis
- Integrate with existing `SocialGraph` wrapper

### Non-Goals

- Unfollowing (network only grows, simplifies analysis)
- Real-time graph recomputation (betweenness recalculated periodically, not every edge)
- Weighted edges (follow is binary)

## Design

Follow decisions occur when an agent engages with content (like/reply/reshare). The decision model considers:

1. **Content resonance** (embedding similarity > 0.7 → +10%)
2. **Social proof** (reshared by followed accounts → +5% per, cap 15%)
3. **Direct engagement** (author replied to agent → +20%)
4. **Reciprocity** (author already follows agent → +10%)
5. **Diminishing returns** (following 200+ → 0.8x multiplier)

Base probability: 5% per engagement

```python
class DynamicSocialGraph(SocialGraph):
    def consider_follow(self, agent_id: str, author_id: str, context: EngagementContext) -> bool:
        """Probabilistically decide whether agent should follow author."""
        ...

    def add_follow(self, follower_id: str, followee_id: str, round_num: int) -> None:
        """Add follow edge with metadata."""
        ...

    def get_follow_history(self, agent_id: str) -> list[FollowEvent]:
        """Get chronological follow events for agent."""
        ...
```

Integration point: Called from `StateUpdateExecutor` after processing agent decisions.

## Tasks

- [ ] Create `DynamicSocialGraph` class extending `SocialGraph`
- [ ] Implement `consider_follow()` with probabilistic decision model
- [ ] Add `FollowEvent` dataclass with round, follower, followee
- [ ] Implement follow history tracking per agent
- [ ] Add `EngagementContext` dataclass for decision inputs
- [ ] Integrate follow decisions into `StateUpdateExecutor`
- [ ] Add per-round follower count tracking for metrics export

## Open Questions

- Should betweenness be recalculated every N rounds or only at simulation end?
- How to handle the case where network becomes too dense (follow probability decay)?
