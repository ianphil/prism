# Twitter Datasets Research

Research notes on available Twitter datasets for PRISM simulation, focusing on datasets with both network topology and content data.

**Research date**: 2026-01-31

## Requirements for PRISM

To simulate X's algorithm realistically, we need:

1. **Network topology**: Follow/follower relationships between users
2. **User profiles**: Interests, traits, metadata for agent generation
3. **Tweet content**: Text, media flags, engagement metrics for RAG seeding
4. **Cascade data**: Retweet/reply chains for validation

## Dataset Survey

### Datasets with Network Data

| Dataset | Nodes | Edges | Network Type | Content | Link |
|---------|-------|-------|--------------|---------|------|
| Higgs Twitter | 456K | 14.8M | Follow + RT + reply + mention | Activity timestamps | [SNAP](https://snap.stanford.edu/data/higgs-twitter.html) |
| SNAP Ego-Twitter | 81K | 1.7M | Follow + ego networks | Node features/profiles | [SNAP](https://snap.stanford.edu/data/ego-Twitter.html) |
| SNAP Twitter 2010 | 41.6M | 1.47B | Follow only | None | [SNAP](https://snap.stanford.edu/data/twitter-2010.html) |
| MPI Twitter | 55M | 1.96B | Follow only | Anonymized, no tweets | [MPI](http://twitter.mpi-sws.org/) |

### Datasets with Tweet Content

| Dataset | Tweets | Users | Content Type | Network | Link |
|---------|--------|-------|--------------|---------|------|
| Sentiment140 | 1.6M | - | Labeled sentiment | None | [Kaggle](https://www.kaggle.com/kazanova/sentiment140) |
| Twitter US Airline | 14.6K | - | Customer complaints | None | [Kaggle](https://www.kaggle.com/crowdflower/twitter-airline-sentiment) |
| COVID-19 Twitter | Varies | Varies | Pandemic discourse | Some have RT networks | Various academic sources |

### Cascade/Virality Datasets

| Dataset | Focus | Data Included | Link |
|---------|-------|---------------|------|
| Higgs Twitter | Viral event cascade | Multi-layer network + activity | [SNAP](https://snap.stanford.edu/data/higgs-twitter.html) |
| Congressional Twitter | Political influence | Weighted influence network | [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10493874/) |
| TwitterTagNet | Hashtag virality | Co-occurrence network + features | [Springer](https://link.springer.com/article/10.1007/s13278-025-01415-0) |

## Higgs Dataset Details

**Best fit for PRISM** - captured during the Higgs boson discovery announcement (July 4, 2012), a natural viral event.

### Network Layers

```
Layer           | Edges      | Description
----------------|------------|----------------------------------
Social (follow) | 14,855,842 | Who follows whom
Retweet         | 418,542    | Who retweeted whom
Reply           | 32,523     | Who replied to whom
Mention         | 150,818    | Who mentioned whom
```

### Files Available

- `higgs-social_network.edgelist.gz` - Follow graph
- `higgs-retweet_network.edgelist.gz` - Retweet cascades
- `higgs-reply_network.edgelist.gz` - Reply network
- `higgs-mention_network.edgelist.gz` - Mention network
- `higgs-activity_time.txt.gz` - Timestamped user activity

### Network Statistics

- **Nodes**: 456,626 users
- **Clustering coefficient**: Varies by layer
- **Captures**: Real viral cascade dynamics

### Limitations

- **No tweet text**: Only network structure and activity timestamps
- **Single event**: Focused on one viral topic (physics/science)
- **2012 data**: Platform dynamics have evolved

## SNAP Ego-Twitter Details

Alternative for smaller-scale experiments with richer node features.

### Data Included

- 973 ego networks (user + their followers)
- Node features (profile attributes)
- Circle/list memberships
- Combined: 81,306 nodes, 1,768,149 edges

### Advantages

- Node features available for trait inference
- Ego network structure useful for community detection
- Smaller scale, faster iteration

### Limitations

- No tweet content
- Sampled around specific ego users
- 2012 data

## Hybrid Approach for PRISM

Given no single dataset has everything, use a **hybrid approach**:

### Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                    PRISM Data Pipeline                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────┐    ┌─────────────────────┐         │
│  │   Higgs Dataset     │    │   Tweet Dataset     │         │
│  │                     │    │   (Sentiment140,    │         │
│  │  • Follow network   │    │    topic-specific)  │         │
│  │  • RT/reply/mention │    │                     │         │
│  │  • Cascade structure│    │  • Tweet text       │         │
│  │  • Activity timing  │    │  • Engagement       │         │
│  └──────────┬──────────┘    │  • User metadata    │         │
│             │               └──────────┬──────────┘         │
│             │                          │                     │
│             ▼                          ▼                     │
│  ┌─────────────────────┐    ┌─────────────────────┐         │
│  │  Network Topology   │    │  Trait Inference    │         │
│  │                     │    │                     │         │
│  │  • SocialGraph      │    │  • KeyBERT/YAKE     │         │
│  │  • In/out-network   │    │  • Stance classifier│         │
│  │  • Cascade patterns │    │  • Interest vectors │         │
│  └──────────┬──────────┘    └──────────┬──────────┘         │
│             │                          │                     │
│             └────────────┬─────────────┘                     │
│                          ▼                                   │
│             ┌─────────────────────────┐                      │
│             │   Agent Profiles        │                      │
│             │                         │                      │
│             │  • ID mapped to network │                      │
│             │  • Traits from tweets   │                      │
│             │  • Follow relationships │                      │
│             └─────────────────────────┘                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Mapping Strategy

1. **Sample Higgs network** to target agent count (250-500)
2. **Preserve network properties** (degree distribution, clustering)
3. **Assign traits** from tweet dataset profiles to network nodes
4. **Match by characteristics** (e.g., high-degree nodes get influencer traits)

### Alternative: Synthetic Generation

If datasets are insufficient:
1. Use Higgs network topology
2. Generate synthetic agent profiles with LLM
3. Seed RAG with LLM-generated posts matching experimental conditions

## Data Access Notes

### Twitter Data Policy

Twitter restricts redistribution of content. Academic datasets typically:
- Share only Tweet IDs (require "hydration" via API)
- Anonymize user identities
- Limit to network structure only

### Recommended Sources

1. **SNAP** (Stanford): https://snap.stanford.edu/data/
2. **Network Repository**: https://networkrepository.com/
3. **Kaggle**: https://www.kaggle.com/ (tweet content datasets)
4. **awesome-twitter-data**: https://github.com/shaypal5/awesome-twitter-data

## References

- Higgs dataset paper: De Domenico et al., "Anatomy of a scientific rumor" (2013)
- SNAP Ego networks: McAuley & Leskovec, "Learning to Discover Social Circles" (2012)
- Twitter 2010: Kwak et al., "What is Twitter, a Social Network or a News Media?" (2010)
