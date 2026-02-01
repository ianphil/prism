---
title: "Data Pipeline: Ingestion and Profile Generation"
status: open
priority: medium
created: 2026-01-27
updated: 2026-01-31
depends_on: ["001-foundation-agent-ollama"]
supports_studies: ["study-network-position-virality.md"]
---

# Data Pipeline: Ingestion and Profile Generation

## Summary

Build the data pipeline for loading Twitter datasets, importing network topology, inferring user traits, and generating agent profiles that bootstrap realistic simulation behavior.

## Motivation

Agent realism depends on grounding in real social media patterns. The PRD emphasizes reproducibility and validation against real data. The X algorithm requires network topology (follow relationships) for in-network vs out-of-network candidate sourcing. This pipeline combines network data with trait inference to create realistic agent populations.

## Research Findings

See `aidocs/twitter-datasets-research.md` for full dataset analysis.

**Key finding**: No single dataset has both complete network topology AND tweet content. Use a **hybrid approach**:

| Dataset | Provides | Missing |
|---------|----------|---------|
| Higgs Twitter (SNAP) | Follow graph, cascade structure | Tweet text, user profiles |
| Tweet datasets (Sentiment140, etc.) | Tweet text, engagement | Network topology |

## Proposal

### Goals

- Import network topology from Higgs dataset (follow graph, cascade structure)
- Load tweet datasets for trait inference (interests, stance, personality)
- Map traits to network nodes using characteristic matching
- Filter bot accounts using available signals
- Generate agent profiles with network position + inferred traits
- Support synthetic generation as fallback option

### Non-Goals

- Real-time web scraping (use pre-loaded datasets only)
- Fine-tuning ML models on custom data
- Handling streaming data ingestion
- Full 456K Higgs network (sample to 250-500 agents)

## Design

### Hybrid Data Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                         Data Sources                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────┐    ┌─────────────────────┐         │
│  │   Higgs Dataset     │    │   Tweet Dataset     │         │
│  │   (SNAP)            │    │   (Sentiment140,    │         │
│  │                     │    │    topic-specific)  │         │
│  │  • Follow edges     │    │                     │         │
│  │  • Retweet edges    │    │  • Tweet text       │         │
│  │  • Reply edges      │    │  • User metadata    │         │
│  │  • Activity timing  │    │  • Engagement       │         │
│  └──────────┬──────────┘    └──────────┬──────────┘         │
│             │                          │                     │
│             ▼                          ▼                     │
│  ┌─────────────────────┐    ┌─────────────────────┐         │
│  │  Network Sampling   │    │  Trait Inference    │         │
│  │                     │    │                     │         │
│  │  • Sample subgraph  │    │  • KeyBERT/YAKE     │         │
│  │  • Preserve degree  │    │  • Stance classifier│         │
│  │  • Keep clustering  │    │  • Personality      │         │
│  └──────────┬──────────┘    └──────────┬──────────┘         │
│             │                          │                     │
│             └────────────┬─────────────┘                     │
│                          ▼                                   │
│             ┌─────────────────────────┐                      │
│             │  Profile Assignment     │                      │
│             │                         │                      │
│             │  Match traits to nodes: │                      │
│             │  • High-degree → influencer traits            │
│             │  • Clusters → similar interests               │
│             │  • Random for remainder │                      │
│             └──────────┬──────────────┘                      │
│                        │                                     │
│                        ▼                                     │
│             ┌─────────────────────────┐                      │
│             │   Agent Population      │                      │
│             │                         │                      │
│             │  • AgentProfile objects │                      │
│             │  • SocialGraph edges    │                      │
│             │  • Ready for simulation │                      │
│             └─────────────────────────┘                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Stage 1: Network Import

Load and sample the Higgs dataset network:

```python
@dataclass
class NetworkData:
    follow_graph: nx.DiGraph      # Who follows whom
    retweet_graph: nx.DiGraph     # Cascade structure (for validation)
    reply_graph: nx.DiGraph       # Conversation structure
    node_metadata: dict[str, NodeStats]  # Degree, clustering, etc.

def load_higgs_network(
    path: Path,
    sample_size: int = 500,
    sampling_method: str = "snowball"  # snowball | random | degree_preserving
) -> NetworkData:
    """Load Higgs edgelists and sample to target size."""
    ...
```

**Sampling methods**:
- `snowball`: Start from seed nodes, expand via connections (preserves local structure)
- `random`: Uniform random node selection (fast, loses structure)
- `degree_preserving`: Sample while maintaining degree distribution

### Stage 2: Trait Inference

Extract traits from tweet dataset:

```python
@dataclass
class InferredTraits:
    user_id: str
    interests: list[str]         # KeyBERT extracted topics
    interest_embedding: list[float]  # For similarity matching
    stance: str                  # Political/topical stance
    personality: dict[str, float]  # Big Five approximation
    activity_level: float        # Posts per day
    influence_score: float       # Based on engagement received

def infer_traits_from_tweets(
    tweets_df: pd.DataFrame,
    user_id_col: str = "user_id",
    text_col: str = "text"
) -> list[InferredTraits]:
    """Extract traits from tweet history per user."""
    ...
```

### Stage 3: Profile Assignment

Map inferred traits to network nodes:

```python
def assign_profiles_to_network(
    network: NetworkData,
    traits_pool: list[InferredTraits],
    strategy: str = "characteristic_match"
) -> list[AgentProfile]:
    """
    Assign traits to network nodes.

    Strategies:
    - characteristic_match: High-degree nodes get influencer traits
    - cluster_coherent: Nodes in same cluster get similar interests
    - random: Random assignment from pool
    """
    ...
```

**Matching heuristics**:
- Nodes with high in-degree → traits from high-engagement users
- Nodes in tight clusters → similar interest profiles
- Bridge nodes → diverse interest profiles

### Stage 4: Agent Profile Generation

```python
@dataclass
class AgentProfile:
    # Identity
    id: str
    name: str

    # Network position (from Higgs)
    in_degree: int
    out_degree: int
    cluster_id: Optional[int]

    # Inferred traits (from tweet dataset)
    interests: list[str]
    interest_embedding: list[float]
    stance: Optional[str]
    personality: dict[str, float]

    # Behavioral parameters
    activity_level: float  # Posts per round probability
    engagement_style: str  # "creator" | "amplifier" | "commenter" | "lurker"

    def to_system_prompt(self) -> str:
        """Generate agent system prompt from profile."""
        ...
```

### Configuration

```yaml
data_pipeline:
  # Network source
  network:
    source: "higgs"  # higgs | synthetic | custom
    higgs:
      path: "data/higgs/"
      layers: ["social", "retweet"]  # Which edge types to load
    sample:
      size: 500
      method: "snowball"
      seed_nodes: 10

  # Trait source
  traits:
    source: "sentiment140"  # sentiment140 | custom | synthetic
    sentiment140:
      path: "data/sentiment140.csv"
    inference:
      interests_model: "keybert"
      stance_model: "cardiffnlp/twitter-roberta-base-stance"

  # Profile assignment
  assignment:
    strategy: "characteristic_match"
    cluster_coherence: 0.7  # How similar should cluster members be

  # Bot filtering (applied to trait source)
  bot_filter:
    enabled: true
    patterns: ["http://", "follow me", "check out"]
    min_unique_words: 10
```

### Fallback: Synthetic Generation

When real data is unavailable or for controlled experiments:

```python
def generate_synthetic_population(
    network: NetworkData,
    topic_distribution: dict[str, float],
    stance_distribution: dict[str, float]
) -> list[AgentProfile]:
    """Generate synthetic profiles matching network structure."""
    ...
```

## Datasets

### Primary: Higgs Twitter (Network)

- **Source**: https://snap.stanford.edu/data/higgs-twitter.html
- **Size**: 456K nodes, 14.8M follow edges
- **Files**:
  - `higgs-social_network.edgelist.gz` - Follow graph
  - `higgs-retweet_network.edgelist.gz` - Retweet cascades
  - `higgs-reply_network.edgelist.gz` - Reply network

### Primary: Sentiment140 (Traits)

- **Source**: https://www.kaggle.com/kazanova/sentiment140
- **Size**: 1.6M tweets, labeled sentiment
- **Use**: Trait inference, interest extraction

### Alternative Tweet Datasets

- Twitter US Airline Sentiment (customer service domain)
- COVID-19 Twitter datasets (health/political discourse)
- Custom topic-specific collections

## Study 1 Validation Phase

Before running simulations, Study 1 requires validating the bridge effect hypothesis using real Higgs cascade data. This is a decision gate for proceeding with the study.

### Validation Analysis

```python
def validate_bridge_effect(higgs_data: NetworkData) -> ValidationResult:
    """
    Analyze Higgs cascades to check if bridge position correlates
    with cascade size for small accounts.

    Decision gate criteria:
    - Proceed if: correlation > 0.1 AND p < 0.10
    - Revise if: correlation <= 0 OR p >= 0.10
    """
    # Load follow graph and retweet cascades
    follow_graph = higgs_data.follow_graph
    retweet_graph = higgs_data.retweet_graph

    # Calculate metrics for each cascade originator
    betweenness = nx.betweenness_centrality(follow_graph)
    follower_counts = dict(follow_graph.in_degree())
    cascade_sizes = dict(retweet_graph.in_degree())

    # Filter to small accounts (bottom 50% by followers)
    median_followers = np.median(list(follower_counts.values()))
    small_accounts = [
        uid for uid, count in follower_counts.items()
        if count <= median_followers and cascade_sizes.get(uid, 0) > 0
    ]

    # Correlate betweenness with cascade size
    x = [betweenness.get(uid, 0) for uid in small_accounts]
    y = [cascade_sizes.get(uid, 0) for uid in small_accounts]

    correlation, p_value = stats.spearmanr(x, y)

    return ValidationResult(
        correlation=correlation,
        p_value=p_value,
        n_small_accounts=len(small_accounts),
        proceed=correlation > 0.1 and p_value < 0.10
    )
```

### Validation Output

```python
@dataclass
class ValidationResult:
    correlation: float
    p_value: float
    n_small_accounts: int
    proceed: bool

    # Descriptive statistics
    small_account_cascade_median: float
    bridge_account_cascade_median: float
    peripheral_account_cascade_median: float
```

## Tasks

### Network Import
- [ ] Implement Higgs edgelist loader (gzipped format)
- [ ] Add network sampling methods (snowball, random, degree-preserving)
- [ ] Compute node metadata (degree, clustering, centrality)
- [ ] Create `SocialGraph` wrapper for agent queries

### Study 1 Validation (Higgs Analysis)
- [ ] Implement `validate_bridge_effect()` function
- [ ] Calculate betweenness centrality for full Higgs network
- [ ] Correlate betweenness with cascade size for small accounts
- [ ] Generate validation report with decision gate outcome
- [ ] Export validation results for study documentation

### Trait Inference
- [ ] Implement tweet dataset loader with schema validation
- [ ] Integrate KeyBERT for interest extraction
- [ ] Add stance classifier using pre-trained transformer
- [ ] Implement bot filtering (patterns, vocabulary diversity)

### Profile Assignment
- [ ] Implement characteristic matching algorithm
- [ ] Add cluster coherence for interest similarity
- [ ] Create `AgentProfile` dataclass with network + trait fields
- [ ] Implement profile-to-prompt generator

### Testing
- [ ] Test network sampling preserves key properties
- [ ] Test trait inference accuracy on labeled data
- [ ] Test profile assignment produces valid agents
- [ ] Integration test: full pipeline from datasets to agent population
