---
title: "Agent Strategy System"
status: open
priority: medium
created: 2026-01-31
depends_on: ["20260131-dynamic-network-module.md", "003-agent-behavior-statecharts"]
supports_studies: ["study-growth-strategies.md"]
---

# Agent Strategy System

## Summary

Enable per-agent behavioral strategies that control posting frequency, reply targeting, and content scope. Allows testing which strategies help small accounts gain followers and improve network position.

## Motivation

Study 2 tests five growth strategies (cross-community content, influencer engagement, peer engagement, high volume, quality focus) against a baseline. This requires agents to behave differently based on assigned strategy, particularly in who they reply to and what content they generate.

## Proposal

### Goals

- Define strategy configurations (post rate, reply rate, reply targeting, content scope)
- Assign strategies to specific "focal agents" while others use baseline
- Implement reply targeting logic (high-follower, similar-size, random)
- Support strategy-specific content generation prompts
- Track strategy execution for analysis

### Non-Goals

- Dynamic strategy switching mid-simulation
- Learning/adaptive strategies
- More than 6 strategy variants (5 + control)

## Design

Strategies are defined as configuration objects and assigned to agents at simulation start:

```python
@dataclass
class AgentStrategy:
    name: str
    post_probability: float = 0.3
    reply_probability: float = 0.2
    reply_target: str = "random"  # random | high_follower | similar_size
    content_scope: str = "own_cluster"  # own_cluster | multi_cluster
    content_quality: str = "normal"  # normal | high

STRATEGIES = {
    "baseline": AgentStrategy("baseline"),
    "cross_community": AgentStrategy("cross_community", content_scope="multi_cluster"),
    "influencer_engagement": AgentStrategy("influencer_engagement", reply_probability=0.4, reply_target="high_follower"),
    "peer_engagement": AgentStrategy("peer_engagement", reply_probability=0.4, reply_target="similar_size"),
    "high_volume": AgentStrategy("high_volume", post_probability=0.6),
    "quality_focus": AgentStrategy("quality_focus", post_probability=0.15, content_quality="high"),
}
```

Reply targeting implementation:

```python
def select_reply_target(agent: Agent, feed: list[Post], strategy: AgentStrategy) -> Optional[Post]:
    match strategy.reply_target:
        case "high_follower":
            candidates = [p for p in feed if get_follower_count(p.author_id) >= 500]
        case "similar_size":
            my_followers = get_follower_count(agent.id)
            candidates = [p for p in feed if abs(get_follower_count(p.author_id) - my_followers) <= 50]
        case "random":
            candidates = feed
    return random.choice(candidates) if candidates else None
```

Integration: Strategy influences `DecisionExecutor` behavior and prompt generation.

## Tasks

- [ ] Define `AgentStrategy` dataclass with all parameters
- [ ] Create `STRATEGIES` registry with 6 preset strategies
- [ ] Implement `select_reply_target()` with targeting logic
- [ ] Add strategy assignment to agent initialization
- [ ] Modify `DecisionExecutor` to use agent strategy for probabilities
- [ ] Implement strategy-specific prompt templates (quality, cross-community)
- [ ] Add strategy execution tracking to metrics (who replied to whom)

## Open Questions

- Should strategy be stored on Agent or looked up from a separate registry?
- How to generate "cross-community" content without knowing all community topics upfront?
