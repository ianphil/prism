# X Algorithm Research

Research notes from exploring X's open-sourced recommendation algorithm repository.

**Source**: https://github.com/twitter/the-algorithm (cloned 2026-01-31)

## Architecture Overview

The For You Timeline uses a multi-stage pipeline:

```
1B+ tweets → Candidate Sourcing → ~1500 candidates
           → Light Ranker (logistic regression) → ~100 candidates
           → Heavy Ranker (neural network) → ~50 candidates
           → Heuristic Rescoring → Final feed
```

### Candidate Sources

| Source | Description | Proportion |
|--------|-------------|------------|
| In-Network (Earlybird) | Posts from followed accounts | ~50% |
| UTEG | User-Tweet Entity Graph traversal | Out-of-network |
| SimClusters | Community detection embeddings | Out-of-network |
| FRS | Follow Recommendation Service | Out-of-network |

Default fetch limits from `ScoredTweetsParam.scala`:
- In-network: 600 tweets
- UTEG: 300 tweets
- Tweet Mixer: 400 tweets
- FRS: 100 tweets

## Rescoring Factor System

Post-ML scoring applies multiplicative heuristic factors. From `RescoringFactorProvider.scala`:

```scala
val scaleFactor = rescorers.map(_(query, candidate)).product
val updatedScore = score * scaleFactor
```

### Core Scale Factors

| Parameter | Default | Description |
|-----------|---------|-------------|
| `OutOfNetworkScaleFactor` | 0.75 | OON tweets scored at 75% |
| `ReplyScaleFactor` | 0.75 | Replies scored at 75% |
| `LiveContentScaleFactor` | 1.0 (max 10000) | Live streams boost |
| `AuthorDiversityDecayFactor` | 0.5 | Repeat author penalty |
| `AuthorDiversityFloor` | 0.25 | Minimum after decay |
| `CandidateSourceDiversityDecayFactor` | 0.9 | Source diversity |
| `CandidateSourceDiversityFloor` | 0.8 | Minimum after decay |

### User Feedback Factors

| Parameter | Default | Description |
|-----------|---------|-------------|
| `ControlAiShowLessScaleFactor` | 0.05 | "Show less" → 5% score |
| `ControlAiShowMoreScaleFactor` | 20.0 | "Show more" → 20x boost |
| `ControlAiEmbeddingSimilarityThreshold` | 0.67 | Similarity for control |

### MTL Normalization

Multi-task learning calibration with parameters:
- Alpha: 100.0 (percentage)
- Beta: 100,000,000
- Gamma: 5,000,000

Applied based on author followers count, retweet status, and reply status.

## Light Ranker Features

From `recap_earlybird/feature_config.py` (in-network model):

### Static Features
- `tweet_age_in_secs` - Tweet age/recency
- `from_verified_account_flag`
- `is_reply_flag`, `is_retweet_flag`
- `has_quote_flag`, `has_trend_flag`
- `text_score` - Quality score from TweetTextScorer
- `user_reputation` - Tweepcred page-rank score

### Media Features
- `has_image_url_flag`
- `has_video_url_flag`
- `has_native_image_flag`
- `has_card_flag`
- `has_link_flag`, `has_visible_link_flag`
- `has_periscope_flag`, `has_vine_flag`
- `has_pro_video_flag`

### Engagement Features (Realtime)
- `favorite_count`, `favorite_count_v2`
- `retweet_count`, `retweet_count_v2`
- `reply_count`, `reply_count_v2`
- `quote_count`
- `weighted_favorite_count`
- `weighted_retweet_count`
- `weighted_reply_count`
- `weighted_quote_count`

### Safety Features
- `is_offensive_flag`
- `is_sensitive_content`
- `label_abusive_hi_rcl_flag`
- `label_nsfw_hi_prc_flag`, `label_nsfw_hi_rcl_flag`
- `label_spam_flag`, `label_spam_hi_rcl_flag`
- `label_dup_content_flag`

### Engagement Labels (Training)
- `is_clicked`
- `is_favorited`
- `is_replied`
- `is_retweeted`
- `is_open_linked`
- `is_photo_expanded`
- `is_profile_clicked`
- `is_video_playback_50`

## Media Feature Extraction

From `TweetMediaFeaturesExtractor.scala`:

```scala
private val ImageCategories = Set(
  ms.MediaCategory.TweetImage.value,
  ms.MediaCategory.TweetGif.value
)
private val VideoCategories = Set(
  ms.MediaCategory.TweetVideo.value,
  ms.MediaCategory.AmplifyVideo.value
)
```

Extracted features include:
- `videoDurationMs`, `bitRate`
- `aspectRatioNum`, `aspectRatioDen`
- `widths`, `heights`
- `viewCount`
- `hasImage`, `hasVideo`
- Face detection areas
- Dominant color palette

## Candidate Signals

From `RETREIVAL_SIGNALS.md`, signals used for candidate sourcing:

| Signal | USS | SimClusters | TwHIN | UTEG | FRS | Light Ranking |
|--------|-----|-------------|-------|------|-----|---------------|
| Author Follow | Features | Features/Labels | Features/Labels | Features | Features/Labels | - |
| Tweet Favorite | Features | Features | Features/Labels | Features | Features/Labels | Features/Labels |
| Retweet | Features | - | Features/Labels | Features | Features/Labels | Features/Labels |
| Tweet Reply | Features | - | Features | Features | Features/Labels | Features |
| Tweet Click | Features | - | - | - | Features | Labels |
| Video Watch | Features | Features | - | - | - | Labels |

## Key Observations

1. **No explicit velocity/media boost multipliers** in the heuristic layer - these effects are learned by the ML models through engagement features normalized by time.

2. **In-network preference** is implemented via the 0.75x out-of-network scale factor, not a boost to in-network content.

3. **Author diversity** uses exponential decay (0.5^n) with a floor (0.25) to prevent author domination.

4. **User feedback** has asymmetric impact: "show less" (0.05x) is a 20x larger effect than "show more" (20x) in absolute terms.

5. **Two separate models** exist for in-network (`recap_earlybird`) and out-of-network (`rectweet_earlybird`) ranking.

6. **Real Graph** drives relationship strength between users for in-network relevance scoring.

## Relevant File Paths

```
home-mixer/server/src/main/scala/com/twitter/home_mixer/
├── product/scored_tweets/
│   ├── param/ScoredTweetsParam.scala          # Configuration parameters
│   ├── scorer/
│   │   ├── HeuristicScorer.scala              # Heuristic scoring pipeline
│   │   └── RescoringFactorProvider.scala      # Scale factor definitions
│   └── candidate_pipeline/                     # Candidate sourcing configs
├── model/HomeFeatures.scala                    # Feature definitions
└── util/tweetypie/content/
    └── TweetMediaFeaturesExtractor.scala       # Media feature extraction

src/python/twitter/deepbird/projects/timelines/
├── configs/recap_earlybird/feature_config.py   # In-network features
└── configs/rectweet_earlybird/feature_config.py # Out-of-network features
```

## Implementation Implications for PRISM

For realistic simulation, the ranking system should:

1. **Split candidates** by in-network (followed) vs out-of-network source
2. **Apply scale factors** as multiplicative modifiers to base similarity scores
3. **Track author frequency** for diversity decay within a feed
4. **Use engagement counts** as features, not explicit boost formulas
5. **Respect the 0.75x OON factor** as the primary in-network preference mechanism

The ML-based scoring can be approximated with embedding similarity, while the heuristic rescoring layer provides the documented multiplicative adjustments.
