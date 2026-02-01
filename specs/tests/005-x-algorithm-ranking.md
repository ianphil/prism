---
target:
  - prism/rag/config.py
  - prism/rag/ranker.py
  - prism/rag/models.py
  - prism/agents/social_agent.py
  - prism/simulation/protocols.py
---

# X Algorithm Ranking Spec Tests

Tests verify that the X algorithm ranking implementation provides realistic feed curation with documented scale factors, candidate sourcing, and author diversity controls.

## Configuration

### RankingConfig model exists with documented scale factors

Researchers need configurable ranking to run controlled experiments. Without a proper config model, scale factors would be hardcoded and experiments would lack reproducibility.

```
Given the prism/rag/config.py file
When examining the RankingConfig class
Then it has a mode field accepting "x_algo", "preference", or "random"
And it has out_of_network_scale field with default 0.75
And it has reply_scale field with default 0.75
And it has author_diversity_decay field with default 0.5
And it has author_diversity_floor field with default 0.25
And all scale factor fields have ge=0.0, le=1.0 validation
```

### RankingConfig validates floor <= decay constraint

Invalid configuration could produce unexpected ranking behavior. The floor must not exceed the decay factor or author diversity calculations break.

```
Given the prism/rag/config.py file
When examining the RankingConfig class
Then it has a model_validator that ensures author_diversity_floor <= author_diversity_decay
And the validator raises ValueError when the constraint is violated
```

### RankingConfig has candidate limit fields

Candidate limits control the balance between in-network and out-of-network content. Without limits, the algorithm could be overwhelmed by one source.

```
Given the prism/rag/config.py file
When examining the RankingConfig class
Then it has in_network_limit field with default 50 and ge=1 validation
And it has out_of_network_limit field with default 50 and ge=1 validation
```

## Social Graph

### SocialGraphProtocol defines required methods

The ranking algorithm needs to distinguish in-network from out-of-network content. Without a social graph protocol, there's no abstraction for follow relationships.

```
Given the prism/simulation/protocols.py file
When examining the SocialGraphProtocol class
Then it defines a get_following method taking agent_id: str returning set[str]
And it defines an is_following method taking follower_id and followee_id returning bool
```

### SocialAgent has following field

Agents need to track who they follow to enable in-network feed generation. Without this field, all content would be treated as out-of-network.

```
Given the prism/agents/social_agent.py file
When examining the SocialAgent class __init__ method
Then it accepts a following parameter of type set[str] with default empty set
And it stores the value in self.following attribute
```

## Post Model

### Post model has parent_id for reply detection

The ranking algorithm applies a reply penalty. Without parent_id, replies cannot be detected and the scale factor cannot be applied.

```
Given the prism/rag/models.py file
When examining the Post class
Then it has a parent_id field of type str | None with default None
And the field is included in the to_metadata method output
And the from_chroma_result method handles parent_id from metadata
```

## XAlgorithmRanker

### XAlgorithmRanker class exists with correct initialization

The ranker is the core component for X-style feed generation. Without it, the simulation cannot produce realistic algorithmic feeds.

```
Given the prism/rag/ranker.py file
When examining the XAlgorithmRanker class
Then it has an __init__ method accepting retriever and config parameters
And it stores the config as an instance attribute
And it has a get_feed method accepting agent and social_graph parameters
```

### XAlgorithmRanker implements candidate sourcing

Feed quality depends on balanced in-network and out-of-network content. Without proper sourcing, feeds would miss the INN/OON distinction that drives X's algorithm.

```
Given the prism/rag/ranker.py file
When examining the XAlgorithmRanker class
Then it has a method to get in-network candidates using the agent's following set
And it has a method to get out-of-network candidates excluding followed authors
And both methods return posts with similarity scores
```

### XAlgorithmRanker applies heuristic rescoring

X's algorithm uses documented scale factors for realistic ranking. Without applying these factors, the simulation would not reflect actual platform behavior.

```
Given the prism/rag/ranker.py file
When examining the XAlgorithmRanker class
Then it applies out_of_network_scale to posts from non-followed authors
And it applies reply_scale to posts where parent_id is not None
And scale factors are multiplied together, not added
```

### XAlgorithmRanker implements author diversity

Feed domination by single authors degrades user experience. X's algorithm penalizes repeat authors to ensure diversity.

```
Given the prism/rag/ranker.py file
When examining the XAlgorithmRanker class
Then it tracks author occurrence count during feed generation
And it applies decay factor exponentially based on occurrence
And it enforces the floor as minimum score after decay
And occurrence tracking resets for each get_feed call
```

### XAlgorithmRanker delegates for non-x_algo modes

Backward compatibility requires existing modes to continue working. The ranker should delegate to the underlying retriever for preference and random modes.

```
Given the prism/rag/ranker.py file
When examining the XAlgorithmRanker.get_feed method
Then when config.mode is "preference" it delegates to retriever.get_feed with mode="preference"
And when config.mode is "random" it delegates to retriever.get_feed with mode="random"
And when config.mode is "x_algo" it runs the full ranking pipeline
```

## Integration

### FeedRetriever provides scores for ranking

The ranker needs similarity scores to apply heuristic rescoring. Without score access, base ranking cannot be computed.

```
Given the prism/rag/retriever.py file
When examining the FeedRetriever class
Then it has a method that returns posts with their distance or similarity scores
And the method includes distances in the ChromaDB query
```
