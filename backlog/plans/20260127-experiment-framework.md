---
title: "Experiment Framework and CLI"
status: open
priority: medium
created: 2026-01-27
updated: 2026-01-31
depends_on: ["004-simulation-workflow-loop", "20260127-x-algorithm-ranking.md", "20260127-observability-metrics.md"]
---

# Experiment Framework and CLI

## Summary

Build the experimentation infrastructure including CLI for running simulations, social network generation, A/B testing framework, batch execution with replications, and DOE integration for multifactorial studies.

## Motivation

PRISM's value is in enabling controlled experiments on virality. The PRD outlines a phased testing approach (A/B MVP → DOE) and requires <5 CLI commands to run a full simulation. This framework makes hypothesis testing accessible to researchers.

## Proposal

### Goals

- Generate synthetic social networks with configurable topology
- Create CLI entry point for running experiments and visualizing results
- Implement A/B/multi-arm experiment runner with configurable scenarios
- Support batch execution with replications (20-50 per condition)
- Integrate pyDOE/SALib for factorial designs and sensitivity analysis
- Enable YAML-driven experiment configuration

### Non-Goals

- Web UI for experiment management
- Distributed execution across multiple machines
- Automated hypothesis generation
- Importing real Twitter follow graphs (Phase 1)

## Design

### Social Network Generation

The X algorithm's in-network preference (0.75x OON scale factor) requires a follow graph between agents. Network topology affects information spread dynamics.

#### Topology Options

| Topology | Description | Use Case |
|----------|-------------|----------|
| **Erdős-Rényi** | Random graph, uniform edge probability | Baseline, null model |
| **Barabási-Albert** | Scale-free, preferential attachment | Realistic social networks |
| **Watts-Strogatz** | Small-world, high clustering | Community structure |
| **Stochastic Block** | Community-based connections | Polarization studies |

#### Network Parameters

```yaml
network:
  topology: "barabasi_albert"  # erdos_renyi | barabasi_albert | watts_strogatz | stochastic_block

  # Topology-specific parameters
  erdos_renyi:
    p: 0.02  # Edge probability

  barabasi_albert:
    m: 3  # Edges per new node (controls density)

  watts_strogatz:
    k: 6  # Each node connected to k nearest neighbors
    p: 0.1  # Rewiring probability

  stochastic_block:
    communities: 5
    p_within: 0.15  # Intra-community edge probability
    p_between: 0.01  # Inter-community edge probability
```

#### Implementation

```python
import networkx as nx

def generate_social_graph(
    agent_ids: list[str],
    config: NetworkConfig
) -> nx.DiGraph:
    n = len(agent_ids)

    match config.topology:
        case "erdos_renyi":
            G = nx.erdos_renyi_graph(n, config.erdos_renyi.p, directed=True)
        case "barabasi_albert":
            G = nx.barabasi_albert_graph(n, config.barabasi_albert.m)
            G = G.to_directed()  # Convert to directed for follow relationships
        case "watts_strogatz":
            G = nx.watts_strogatz_graph(n, config.watts_strogatz.k, config.watts_strogatz.p)
            G = G.to_directed()
        case "stochastic_block":
            sizes = [n // config.stochastic_block.communities] * config.stochastic_block.communities
            probs = build_block_matrix(config.stochastic_block)
            G = nx.stochastic_block_model(sizes, probs, directed=True)

    # Relabel nodes to agent IDs
    mapping = {i: agent_ids[i] for i in range(n)}
    return nx.relabel_nodes(G, mapping)
```

#### Network Metrics

Track network properties for experiment analysis:

- **Density**: Edge count / possible edges
- **Clustering coefficient**: Local connectivity
- **Average path length**: Degrees of separation
- **Degree distribution**: In-degree, out-degree histograms
- **Assortativity**: Homophily by agent attributes

### CLI Interface

Per PRD §5, the framework supports phased experimentation:

```bash
# Single simulation run
prism run <config.yaml>

# Batch experiment with replications
prism experiment <experiment.yaml>

# Analyze results
prism analyze <output_dir>

# Network visualization
prism network <config.yaml> --visualize
```

### Experiment Runner

1. Load experiment config (scenarios, variables, replications)
2. Generate social network (or load from checkpoint)
3. Execute simulations with random seeds for reproducibility
4. Aggregate results across replications

### Experiment Configuration

```yaml
experiment:
  name: "visuals_hypothesis_v1"
  replications: 30

  # Network is generated once per experiment
  network:
    topology: "barabasi_albert"
    barabasi_albert:
      m: 3

  # Scenarios define variable combinations
  scenarios:
    - name: "random_no_media"
      ranking_mode: "random"
      seed_post_has_media: false

    - name: "random_with_media"
      ranking_mode: "random"
      seed_post_has_media: true

    - name: "x_algo_no_media"
      ranking_mode: "x_algo"
      seed_post_has_media: false

    - name: "x_algo_with_media"
      ranking_mode: "x_algo"
      seed_post_has_media: true

  # Fixed parameters across all scenarios
  fixed:
    agents: 250
    rounds: 50

  # Seed management
  seeds:
    network_seed: 42  # Same network across scenarios
    simulation_seeds: "sequential"  # 1, 2, 3, ... for replications
```

### A/B Framework

Compare conditions (e.g., visuals × feed mode → 2×2 design):

```python
@dataclass
class ExperimentResult:
    scenario: str
    replication: int
    seed: int

    # Cascade metrics
    cascade_size: int
    cascade_depth: int
    time_to_virality: Optional[int]

    # Network metrics
    spread_velocity: float
    reach_percentage: float
```

### DOE Integration

For Phase 2 multifactorial studies:

- pyDOE for factorial/Latin Hypercube designs
- SALib for Sobol sensitivity indices
- Support for fractional factorial when full factorial is too large

### Analysis Pipeline

```bash
prism analyze outputs/visuals_v1/ --stats --plots
```

Outputs:
- Descriptive stats (medians, SD, distributions)
- Statistical tests (Mann-Whitney U, Kruskal-Wallis)
- Effect sizes (Cohen's d, rank-biserial correlation)
- Cascade visualizations (NetworkX graphs)
- Network topology summary

## Tasks

### Network Generation
- [ ] Define `NetworkConfig` dataclass with topology parameters
- [ ] Implement `generate_social_graph()` with NetworkX
- [ ] Add `SocialGraph` wrapper class for follow relationship queries
- [ ] Implement network metrics collection (density, clustering, assortativity)
- [ ] Add network visualization command

### CLI
- [ ] Create CLI entry point with Click/Typer (`prism/cli/main.py`)
- [ ] Implement `prism run` command for single simulation execution
- [ ] Implement `prism network` command for graph generation/visualization

### Experimentation
- [ ] Define experiment YAML schema (scenarios, variables, replications, seeds)
- [ ] Implement experiment runner with batch execution and seed management
- [ ] Add `prism experiment` command for multi-scenario runs
- [ ] Integrate pyDOE for factorial/Latin Hypercube designs

### Analysis
- [ ] Implement `prism analyze` with stats (Mann-Whitney, Cohen's d)
- [ ] Add cascade visualization with NetworkX
- [ ] Export results to JSON/CSV for external analysis
