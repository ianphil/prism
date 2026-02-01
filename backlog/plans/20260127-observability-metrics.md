---
title: "Observability and Metrics"
status: open
priority: medium
created: 2026-01-27
updated: 2026-01-31
depends_on: ["004-simulation-workflow-loop"]
supports_studies: ["study-network-position-virality.md"]
---

# Observability and Metrics

## Summary

Integrate OpenTelemetry for tracing agent decisions and state transitions, implement virality metrics (cascade size, depth, resharing rates), and add visualization capabilities for experiment analysis.

## Motivation

The PRD targets 100% trace coverage for agent decisions. Researchers need to understand why cascades form, debug unexpected behavior, and validate simulation realism. Metrics like homophily and cascade depth are core outputs for hypothesis testing.

## Proposal

### Goals

- Configure OpenTelemetry tracing via Agent Framework's built-in integration
- Export traces to Jaeger/Zipkin for development visualization
- Implement virality metrics: cascade size, depth, resharing rates, time-to-virality
- Add network analysis metrics: homophily (assortativity) via NetworkX
- Create visualization utilities for cascade graphs and metric plots

### Non-Goals

- Production monitoring infrastructure
- Real-time dashboards
- Custom tracing backends

## Design

Per PRD §4.7, observability wraps around the simulation workflow:

1. **OpenTelemetry Setup**
   - Enable Agent Framework's built-in tracing
   - Configure exporter for Jaeger (development) or JSON (batch analysis)
   - Span per agent decision, tool call, and state transition
2. **Metrics Collection**
   - Per-round: engagement rates, active agents, new posts
   - Per-cascade: size, depth, velocity, reshare tree structure
   - Per-simulation: homophily coefficient, virality threshold detection
3. **Cascade Tracking**: NetworkX graph of reshare relationships
4. **Visualization**: Matplotlib for metric plots, NetworkX for cascade graphs
5. **Export**: JSON/CSV for external analysis tools (pyDOE/SALib integration)

### Study 1 Metrics (Network Position Virality)

Additional metrics required for the network position study:

#### Cross-Community Spread

Track how cascades spread across community boundaries:

```python
def measure_cross_community_spread(
    cascade_graph: nx.DiGraph,
    community_membership: dict[str, int]
) -> dict:
    """Measure cascade spread across communities."""
    communities_reached = set()
    spread_by_round = []

    for node in cascade_graph.nodes():
        community = community_membership.get(node)
        if community is not None:
            communities_reached.add(community)

    # Track which round each community was first reached
    first_reach = {}
    for node, data in cascade_graph.nodes(data=True):
        community = community_membership.get(node)
        round_num = data.get("reshare_round", 0)
        if community not in first_reach or round_num < first_reach[community]:
            first_reach[community] = round_num

    return {
        "communities_reached": len(communities_reached),
        "community_ids": list(communities_reached),
        "first_reach_by_community": first_reach,
    }
```

#### Influencer Capture

Detect when high-follower accounts reshare content:

```python
@dataclass
class InfluencerCaptureMetrics:
    captured: bool  # Did any influencer reshare?
    first_influencer_round: Optional[int]  # When did first influencer reshare?
    influencer_count: int  # How many influencers reshared?
    influencer_ids: list[str]  # Which influencers reshared?

def measure_influencer_capture(
    cascade_graph: nx.DiGraph,
    follower_counts: dict[str, int],
    influencer_threshold: int = 500
) -> InfluencerCaptureMetrics:
    """Track influencer participation in cascade."""
    influencers = []

    for node, data in cascade_graph.nodes(data=True):
        if follower_counts.get(node, 0) >= influencer_threshold:
            influencers.append({
                "id": node,
                "round": data.get("reshare_round"),
                "followers": follower_counts[node],
            })

    influencers.sort(key=lambda x: x["round"] or float("inf"))

    return InfluencerCaptureMetrics(
        captured=len(influencers) > 0,
        first_influencer_round=influencers[0]["round"] if influencers else None,
        influencer_count=len(influencers),
        influencer_ids=[i["id"] for i in influencers],
    )
```

#### Cascade Pathway Analysis

Track the path from seed to key reshares:

```python
def analyze_cascade_pathway(
    cascade_graph: nx.DiGraph,
    seed_author: str,
    target_nodes: list[str]  # e.g., influencers who reshared
) -> dict:
    """Analyze how content reached target nodes from seed."""
    pathways = {}

    for target in target_nodes:
        if nx.has_path(cascade_graph, seed_author, target):
            path = nx.shortest_path(cascade_graph, seed_author, target)
            pathways[target] = {
                "path": path,
                "hops": len(path) - 1,
                "intermediaries": path[1:-1],
            }

    return pathways
```

#### Complete Cascade Metrics

```python
@dataclass
class CascadeMetrics:
    # Core metrics
    cascade_size: int
    cascade_depth: int
    reach_percentage: float

    # Timing metrics
    time_to_10_percent: Optional[int]
    time_to_first_influencer: Optional[int]

    # Spread metrics
    cross_community_spread: int  # Number of communities reached
    community_ids_reached: list[int]

    # Influencer metrics
    influencer_captured: bool
    influencer_count: int
    influencer_capture_round: Optional[int]

    # Pathway metrics
    pathway_to_first_influencer: Optional[list[str]]
```

## Tasks

### OpenTelemetry Integration
- [ ] Configure OpenTelemetry with Jaeger exporter
- [ ] Add tracing spans to workflow executors (feed, decision, state, logging)

### Core Cascade Tracking
- [ ] Implement cascade tracking with NetworkX directed graph
- [ ] Store reshare round on cascade graph nodes
- [ ] Calculate virality metrics (size, depth, velocity, time-to-N-reshares)
- [ ] Calculate network metrics (homophily/assortativity coefficient)

### Study 1 Metrics (Network Position Virality)
- [ ] Implement `measure_cross_community_spread()` function
- [ ] Implement `measure_influencer_capture()` function
- [ ] Implement `analyze_cascade_pathway()` function
- [ ] Define `CascadeMetrics` dataclass with all study metrics
- [ ] Track community membership in cascade analysis
- [ ] Track follower counts for influencer detection

### Visualization
- [ ] Add cascade graph visualization with community coloring
- [ ] Add cascade pathway visualization (seed → influencer paths)
- [ ] Add engagement plots (per-round cascade growth)

### Export
- [ ] Implement JSON/CSV export for metrics and traces
- [ ] Export cascade graph as GraphML for external analysis
