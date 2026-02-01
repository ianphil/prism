# Study Design: Growth Strategies for Small Accounts

Pre-registration style study design following OSF guidelines.

**Template reference**: https://osf.io/prereg/

**Version**: 2.0 (Revised based on methodological review)

---

## 1. Have any data been collected for this study already?

No. This study requires dynamic network simulation capabilities not yet implemented.

**Prerequisite**: Study 1 (network-position-virality) must validate that bridge position provides viral advantage before proceeding. See Section 8 for quantitative decision criteria.

## 2. What's the main question being asked or hypothesis being tested?

**Research Question**: Which behavioral strategies most effectively help small peripheral accounts gain followers and transition toward bridge positions under X's algorithm?

### Primary Hypotheses

| ID | Strategy | Hypothesis | Minimum Effect Size |
|----|----------|------------|---------------------|
| H1 | Cross-community content | Accounts posting content appealing to multiple communities gain at least 30% more followers than baseline, with followers from >=3 communities | d = 0.5 |
| H2 | Influencer engagement | Accounts that reply to high-follower users gain at least 40% more followers than baseline (visibility through association) | d = 0.6 |
| H3 | Peer engagement | Accounts that reply to similar-sized peers achieve higher follow-back rates (>=20%) than influencer engagement (<5%) | Odds ratio = 4.0 |
| H4 | High volume | Accounts posting 2x more frequently gain at least 25% more followers than baseline | d = 0.4 |
| H5 | Quality focus | Accounts posting higher-engagement content gain more followers per post (>=50% higher conversion rate) despite lower volume | Rate ratio = 1.5 |

**Exploratory Question**: Do strategies interact? (e.g., cross-community + influencer engagement)

### Decomposed Hypotheses for Mechanism Isolation

To address strategy confounding, we add auxiliary hypotheses:

- **H2a**: The influencer engagement effect is primarily due to reply targeting (not reply volume)
- **H3a**: The peer engagement effect is primarily due to reciprocity (not reply volume)

These are tested via the High-Reply-Random condition (see Section 4).

## 3. Describe the key dependent variable(s)

**Primary DV**: Follower growth (net new followers over simulation)
- Definition: followers_end - followers_start
- Measurement: Count

**Secondary DVs**:

| Variable | Definition | Measurement | Analysis |
|----------|------------|-------------|----------|
| Follower growth rate | Followers gained per round | followers_gained / rounds_active | ANOVA |
| Betweenness change | Position improvement | betweenness_end - betweenness_start | ANOVA |
| Bridge transition | Crossed bridge threshold (top 10% betweenness) | Binary | Chi-square |
| Time to +50 followers | Rounds to gain 50 followers | Integer or NA | Survival |
| Community diversity | Followers from how many communities | Integer 1-5 | Kruskal-Wallis |
| Follow-back rate | Proportion of engagements that led to follows | Ratio 0-1 | ANOVA |

**Note**: Follower growth is the single primary DV. All others are secondary to avoid Type I error inflation from multiple primary outcomes.

## 4. How many and which conditions will participants be assigned to?

**Design**: Between-subjects with 6 strategy conditions + 1 control + 1 decomposition control

### Strategy Operationalization

**Control: Baseline behavior**
```yaml
strategy: baseline
post_probability: 0.3        # 30% chance to post per round
reply_probability: 0.2       # 20% chance to reply to feed content
reply_target: "random"       # No targeting preference
content_scope: "own_cluster" # Content matches own interests only
```

**Strategy 1: Cross-community content**
```yaml
strategy: cross_community
post_probability: 0.3
reply_probability: 0.2
reply_target: "random"
content_scope: "multi_cluster"  # Content designed to appeal to 2-3 communities
# Operationalized: Post embeddings have high similarity to multiple cluster centroids
```

**Strategy 2: Influencer engagement**
```yaml
strategy: influencer_engagement
post_probability: 0.3
reply_probability: 0.4        # More replies
reply_target: "high_follower" # Target accounts with >500 followers
content_scope: "own_cluster"
```

**Strategy 3: Peer engagement**
```yaml
strategy: peer_engagement
post_probability: 0.3
reply_probability: 0.4        # More replies
reply_target: "similar_size"  # Target accounts within +/-50 followers
content_scope: "own_cluster"
```

**Strategy 4: High volume**
```yaml
strategy: high_volume
post_probability: 0.6         # 2x posting rate
reply_probability: 0.2
reply_target: "random"
content_scope: "own_cluster"
```

**Strategy 5: Quality focus**
```yaml
strategy: quality_focus
post_probability: 0.15        # Half the posting rate
reply_probability: 0.2
reply_target: "random"
content_scope: "own_cluster"
content_quality: "high"       # LLM generates more thoughtful/engaging content
# Operationalized: Longer prompt, request for insight/humor/value-add
```

**NEW - Strategy 6: High-Reply Random (Decomposition Control)**
```yaml
strategy: high_reply_random
post_probability: 0.3
reply_probability: 0.4        # Same reply rate as influencer/peer
reply_target: "random"        # But random targeting
content_scope: "own_cluster"
```

This condition isolates the effect of reply volume from reply targeting. Comparing:
- Influencer engagement vs High-Reply-Random: Tests targeting effect (holding volume constant)
- Peer engagement vs High-Reply-Random: Tests reciprocity effect (holding volume constant)
- High-Reply-Random vs Baseline: Tests pure volume effect

### Focal Agent Design (Revised)

To address non-independence concerns, we reduce focal agents per simulation:

**Design**:
1. Generate network with natural distribution of positions/sizes
2. Select **5 focal agents** per condition (small, peripheral accounts) per simulation
3. Assign strategy to focal agents only
4. Other agents behave naturally (baseline)
5. Track focal agents' growth over simulation

**Selection criteria for focal agents**:
- Followers: 30-70 (small but not isolated)
- Betweenness: bottom 50% (peripheral)
- Active: baseline post_probability >= 0.2
- **Spatial separation**: Selected focal agents must not be direct connections (reduces interaction between focal agents)

**Total focal agents per simulation**: 7 conditions x 5 agents = 35 focal agents
**Simulation runs**: 50 replications (increased from 10)
**Total observations**: 35 x 50 = 1,750 focal agent trajectories

### Verification of Strategy Execution

For each strategy, we will verify that agents actually executed the assigned behavior:

| Strategy | Verification Metric | Threshold |
|----------|---------------------|-----------|
| Cross-community | Mean communities targeted per post | >= 2.0 |
| Influencer engagement | % replies to >500 follower accounts | >= 70% |
| Peer engagement | % replies to +/-50 follower accounts | >= 70% |
| High volume | Posts per 100 rounds | >= 50 |
| Quality focus | Posts per 100 rounds | <= 20 |
| High-reply random | Replies per 100 rounds | >= 35 |

Agents failing verification thresholds are flagged for sensitivity analysis.

## 5. Specify exactly which analyses you will conduct

### Primary Analysis: Linear Mixed-Effects Model

To account for agents nested within simulations:

```
follower_growth ~ strategy + (1 | simulation_id)
```

**Model specification**:
- Fixed effect: strategy (7 levels, baseline as reference)
- Random effect: simulation_id (intercept only)
- Estimation: REML
- Software: R lme4 or Python statsmodels

**Inference**:
- Likelihood ratio test comparing model with and without strategy
- alpha = 0.05 for omnibus test

**Post-hoc**: Estimated marginal means with Tukey adjustment for pairwise comparisons

**Effect size**:
- Marginal R-squared (fixed effects only)
- Conditional R-squared (fixed + random)
- Cohen's d for pairwise comparisons (using pooled residual SD)

### Planned Contrasts (Protected)

Contrasts are only conducted if the omnibus test is significant (p < 0.05). Holm-Bonferroni correction is applied to the 5 contrasts.

| Contrast | Comparison | Tests | Expected Direction |
|----------|------------|-------|-------------------|
| C1 | All strategies vs Control | Do strategies help at all? | Strategies > Control |
| C2 | Influencer vs Peer engagement | Punching up vs lateral | Directional (exploratory) |
| C3 | High volume vs Quality focus | Quantity vs quality | Directional (exploratory) |
| C4 | Cross-community vs single-cluster strategies | Content breadth | Cross > Single |
| C5 | Influencer vs High-Reply-Random | Targeting effect | Influencer > Random |

### Secondary Analyses

**Bridge transition**: Mixed-effects logistic regression
```
bridge_transition ~ strategy + (1 | simulation_id)
```
Report odds ratios with 95% CI.

**Betweenness change**: Same mixed-effects structure as follower growth

**Growth curves**: Mixed-effects model with time x strategy interaction
```
follower_count ~ time * strategy + (1 + time | agent_id) + (1 | simulation_id)
```
This models individual growth trajectories with random slopes.

**Power analysis for bridge transition** (secondary outcome):
- Assuming baseline transition rate of 5%
- To detect increase to 15% with 80% power, need ~140 per group
- With 250 per group (5 x 50), we are adequately powered for 10% to 15% differences

### Exploratory Analyses

- Correlation: engagement received x follower growth
- Mediation: Does visibility (impressions) mediate strategy -> growth?
- Interaction: strategy x starting_position
- Strategy execution fidelity analysis

## 6. Describe exactly how outliers will be defined and handled

**Outlier definition**: Focal agents with follower growth beyond 3x IQR from condition median.

**Handling**:
1. Primary analysis includes all focal agents
2. Sensitivity analysis with outliers winsorized to 3x IQR boundary
3. Investigate outliers qualitatively (what happened?)

**Exclusions**:
- Focal agents who become inactive (0 posts for 20+ consecutive rounds AND post_probability >= 0.15): excluded
- **Clarification**: Quality focus agents (post_probability = 0.15) are only excluded if inactive for 30+ consecutive rounds (adjusted for lower expected activity)
- Expected exclusion rate: <5%

**Strategy execution failures**: Agents failing verification thresholds (Section 4) are:
1. Included in primary analysis (intent-to-treat)
2. Excluded in per-protocol sensitivity analysis

## 7. How many observations will be collected or what will determine sample size?

**Focal agents per condition**: 5
**Conditions**: 7 (including new High-Reply-Random)
**Focal agents per simulation**: 35
**Simulation runs**: 50 replications
**Total observations**: 35 x 50 = 1,750 focal agent trajectories
**Observations per condition**: 250

**Simulation length**: 100 rounds (longer than Study 1 to allow growth)

### Power Analysis (ICC-Adjusted)

**Assumptions**:
- Expected ICC (intra-class correlation): 0.10 (estimated from pilot; agents in same network share ~10% of variance)
- Cluster size: 5 agents per condition per simulation
- Number of clusters: 50 simulations
- Design effect: 1 + (5-1) x 0.10 = 1.4

**Effective sample size per condition**: 250 / 1.4 = 179 effective observations

**Power calculation**:
- For mixed-effects model detecting medium effect (d = 0.5)
- With 179 effective observations per group, 7 groups
- alpha = 0.05, two-tailed
- Power > 0.90

**Sensitivity**: If ICC is higher (0.20), effective n = 250/1.8 = 139, still >80% power for d = 0.5.

**Stopping rule**: All 50 replications complete. No interim analyses.

## 8. Anything else you would like to pre-register?

### Decision Criteria for Study 1 -> Study 2 Gate

This study should only proceed if Study 1 demonstrates that bridge position provides value. Quantitative criteria from Study 1:

**Proceed to Study 2 if ANY of the following are met**:
1. **Equivalence established**: TOST shows Small-Bridge approximately equal to Large-Peripheral (p < 0.05)
2. **Bridge effect significant**: Bridge positions show significantly larger cascades than peripheral positions (main effect in ART-ANOVA, p < 0.05, epsilon-squared > 0.06)
3. **Correlation threshold**: Spearman's rho (betweenness x cascade size) > 0.25 across all agents

**Do not proceed if**:
- Bridge position shows no advantage (main effect p > 0.10)
- AND follower count entirely dominates (size main effect epsilon-squared > 0.20, position epsilon-squared < 0.02)

If results are ambiguous, proceed with Study 2 labeled as exploratory.

### Quality Focus Validation Plan

Before running the full experiment, validate that the "quality focus" prompt actually produces higher-quality content.

**Validation procedure**:

1. **Content generation**: Generate 100 posts using baseline prompt and 100 posts using quality focus prompt (same agent profiles)

2. **Independent rating**:
   - Use a separate LLM (different from simulation agents) to rate posts on:
     - Insight/novelty (1-5)
     - Conversation potential (1-5)
     - Value to reader (1-5)
   - Also calculate objective metrics:
     - Lexical diversity (type-token ratio)
     - Specificity (named entities, concrete nouns)
     - Question inclusion (binary)

3. **Validation threshold**: Quality focus posts must score significantly higher (p < 0.05) on at least 2 of 3 rating dimensions AND show higher lexical diversity

4. **If validation fails**: Revise quality prompt and re-validate, OR drop H5 and proceed with remaining hypotheses

**Manipulation check during simulation**: Track per-post engagement rates. Quality focus posts should receive higher mean engagement per post (not total engagement due to lower volume).

### Dynamic Network Model

**Follow decision model**: After each round, agents may follow accounts whose content they engaged with.

```python
def consider_following(agent, post_author, context):
    """Called when agent engages with (likes/replies/reshares) a post."""

    if agent.already_follows(post_author):
        return False

    # Base probability from engagement
    p = 0.05

    # Content resonance: post matched agent's interests
    similarity = cosine_similarity(post.embedding, agent.interest_embedding)
    if similarity > 0.7:
        p += 0.10

    # Social proof: author was reshared by accounts agent follows
    reshare_count = count_reshares_by_following(post_author, agent)
    p += min(reshare_count * 0.05, 0.15)  # Cap at +0.15

    # Direct engagement: author replied to agent
    if author_replied_to_agent(post_author, agent, this_round=True):
        p += 0.20

    # Reciprocity: agent follows accounts that follow them
    if post_author.follows(agent):
        p += 0.10

    # Diminishing returns: less likely to follow if already following many
    if agent.following_count > 200:
        p *= 0.8

    return random.random() < p
```

### Sensitivity Analysis for Follow Model Parameters

The follow decision model has multiple researcher-specified parameters. We will conduct sensitivity analysis varying key parameters:

| Parameter | Default | Low | High | Rationale |
|-----------|---------|-----|------|-----------|
| Base probability | 0.05 | 0.02 | 0.10 | Range based on Twitter follow-back studies |
| Similarity threshold | 0.7 | 0.5 | 0.9 | Tests interest-matching strictness |
| Similarity bonus | 0.10 | 0.05 | 0.20 | Tests content resonance strength |
| Social proof cap | 0.15 | 0.10 | 0.25 | Tests viral exposure effect |
| Direct engagement bonus | 0.20 | 0.10 | 0.30 | Tests reciprocity strength |
| Reciprocity bonus | 0.10 | 0.05 | 0.20 | Tests mutual follow tendency |
| Diminishing factor | 0.80 | 0.60 | 0.95 | Tests saturation effect |

**Procedure**:
1. Run primary analysis with default parameters
2. Rerun with "low" parameters (all set to low values)
3. Rerun with "high" parameters (all set to high values)
4. Report whether conclusions change across parameter sets

**Robustness criterion**: Conclusions are considered robust if the rank ordering of strategies by effectiveness is consistent across parameter sets, even if absolute effect sizes differ.

**Unfollow model**: For simplicity, no unfollowing in this study. Network only grows.

**Acknowledged limitation**: Real networks have churn. Results may overestimate long-term growth by ignoring unfollows. Future studies should add unfollow dynamics.

### Network Configuration (Aligned with Study 1)

```yaml
network:
  topology: "stochastic_block"
  stochastic_block:
    communities: 5
    agents_per_community: 100
    p_within: 0.12          # Aligned with Study 1
    p_between: 0.008        # Aligned with Study 1

  # Initial follower distribution (power law)
  follower_distribution:
    type: "power_law"
    exponent: 2.1           # Realistic social network skew
    min_followers: 10
    max_followers: 5000
```

**Rationale for alignment**: Using identical network parameters as Study 1 ensures that the value of bridge position established in Study 1 applies directly to Study 2. This allows direct comparison: "Study 1 showed bridges achieve X% more spread; Study 2 shows strategy Y helps achieve bridge status."

### Content Generation for Strategies

**Cross-community content**:
```python
def generate_cross_community_post(agent, communities):
    # Select 2-3 communities to target
    target_communities = random.sample(communities, k=random.randint(2, 3))

    # Generate content that bridges topics
    prompt = f"""
    Write a tweet that would interest people in these communities:
    {[c.description for c in target_communities]}

    Find a connection or angle that bridges these topics.
    """
    return llm.generate(prompt)
```

**Quality focus content**:
```python
def generate_quality_post(agent):
    prompt = f"""
    Write a thoughtful tweet about {agent.interests}.

    Make it:
    - Insightful or surprising
    - Conversation-starting (ask a question or make a claim)
    - Valuable to readers (teach something, share experience)

    Take your time to craft something worth sharing.
    """
    return llm.generate(prompt)
```

### Metrics Collection

Per focal agent, per round:
```python
@dataclass
class FocalAgentMetrics:
    round: int
    agent_id: str
    strategy: str
    simulation_id: int  # Added for clustering

    # Growth metrics
    follower_count: int
    follower_change: int
    following_count: int

    # Position metrics
    betweenness_centrality: float
    community_ids_of_followers: list[int]

    # Activity metrics
    posts_this_round: int
    replies_this_round: int
    engagement_received: int  # likes + replies + reshares on their content

    # Strategy execution verification
    reply_targets: list[str]  # Who did they reply to
    reply_target_sizes: list[int]  # Follower counts of reply targets
    content_communities: list[int]  # Which communities did content target

    # Quality metrics (for quality focus validation)
    engagement_per_post: float  # engagement_received / posts if posts > 0
```

### Reporting Intra-Class Correlation

We will report:
1. Estimated ICC from the primary mixed-effects model
2. Comparison to assumed ICC (0.10) used in power analysis
3. If observed ICC > 0.15, discuss implications for effective sample size

## 9. Type of study

**Study type**: Computational simulation experiment with dynamic network evolution

**Relationship to Study 1**:
- Study 1 establishes that bridge position provides viral advantage (static network)
- Study 2 investigates how to achieve bridge position (dynamic network)
- Together: "Being a bridge helps, and here's how to become one"

---

## Implementation Requirements

This study requires capabilities beyond current PRISM implementation:

| Requirement | Current State | Needed |
|-------------|--------------|--------|
| Dynamic follow graph | Fixed topology | Edges added per round |
| Follow decision model | N/A | Probabilistic model (see above) |
| Strategy-differentiated agents | Uniform behavior | Per-agent strategy config |
| Longer simulations | 50 rounds | 100 rounds |
| Per-round network metrics | End-state only | Longitudinal tracking |
| Quality content generation | Single prompt | Strategy-specific prompts |

**Estimated implementation**: Extends Feature 005 (Experiment Framework) with dynamic network module.

---

## References

- Ferraro, F., et al. (2024). Agent-Based Modelling Meets Generative AI. arXiv:2411.16031
- Barabasi, A.-L. (2016). Network Science. Cambridge University Press. (Preferential attachment, power laws)
- Centola, D. (2010). The spread of behavior in an online social network experiment. Science.
- Bates, D., et al. (2015). Fitting Linear Mixed-Effects Models Using lme4. Journal of Statistical Software.
- Lakens, D. (2013). Calculating and reporting effect sizes. Frontiers in Psychology.

## Appendix A: Strategy Summary Table (Revised)

| Strategy | Post Rate | Reply Rate | Reply Target | Content Scope | Hypothesis | New in v2.0 |
|----------|-----------|------------|--------------|---------------|------------|-------------|
| Baseline | 0.3 | 0.2 | Random | Own cluster | Control | No |
| Cross-community | 0.3 | 0.2 | Random | Multi-cluster | H1: Diverse followers | No |
| Influencer engagement | 0.3 | 0.4 | High-follower | Own cluster | H2: Visibility boost | No |
| Peer engagement | 0.3 | 0.4 | Similar-size | Own cluster | H3: Reciprocal follows | No |
| High volume | 0.6 | 0.2 | Random | Own cluster | H4: More visibility | No |
| Quality focus | 0.15 | 0.2 | Random | Own cluster | H5: Better conversion | No |
| **High-reply random** | 0.3 | **0.4** | **Random** | Own cluster | Decomposition control | **Yes** |

## Appendix B: ICC Estimation and Design Effect

```python
import statsmodels.api as sm
from statsmodels.regression.mixed_linear_model import MixedLM

def estimate_icc(data):
    """
    Estimate ICC from mixed-effects model.

    Args:
        data: DataFrame with follower_growth, strategy, simulation_id

    Returns:
        ICC estimate and confidence interval
    """
    # Fit null model (no fixed effects except intercept)
    model = MixedLM.from_formula(
        "follower_growth ~ 1",
        groups="simulation_id",
        data=data
    )
    result = model.fit()

    # Extract variance components
    var_between = result.cov_re.iloc[0, 0]  # Random intercept variance
    var_within = result.scale  # Residual variance

    # Calculate ICC
    icc = var_between / (var_between + var_within)

    # Design effect
    cluster_size = 5  # focal agents per condition per simulation
    design_effect = 1 + (cluster_size - 1) * icc
    effective_n = len(data) / design_effect

    return {
        'icc': icc,
        'var_between': var_between,
        'var_within': var_within,
        'design_effect': design_effect,
        'effective_n_per_condition': effective_n / 7  # 7 conditions
    }
```

## Appendix C: Quality Focus Validation Protocol

```python
def validate_quality_prompts(n_samples=100):
    """
    Pre-experiment validation of quality focus content generation.
    """
    # Generate sample posts
    baseline_posts = [generate_baseline_post(random_agent()) for _ in range(n_samples)]
    quality_posts = [generate_quality_post(random_agent()) for _ in range(n_samples)]

    # LLM rating (using separate model)
    def rate_post(post):
        prompt = f"""
        Rate this tweet on three dimensions (1-5 scale):

        Tweet: {post}

        1. Insight/Novelty: Does it offer a new perspective or information?
        2. Conversation Potential: Would people want to reply to this?
        3. Value to Reader: Does it teach, entertain, or help?

        Return JSON: {{"insight": X, "conversation": X, "value": X}}
        """
        return json.loads(rating_llm.generate(prompt))

    baseline_ratings = [rate_post(p) for p in baseline_posts]
    quality_ratings = [rate_post(p) for p in quality_posts]

    # Objective metrics
    def lexical_diversity(text):
        tokens = text.lower().split()
        return len(set(tokens)) / len(tokens) if tokens else 0

    baseline_diversity = [lexical_diversity(p) for p in baseline_posts]
    quality_diversity = [lexical_diversity(p) for p in quality_posts]

    # Statistical tests
    results = {
        'insight': stats.mannwhitneyu(
            [r['insight'] for r in quality_ratings],
            [r['insight'] for r in baseline_ratings],
            alternative='greater'
        ),
        'conversation': stats.mannwhitneyu(
            [r['conversation'] for r in quality_ratings],
            [r['conversation'] for r in baseline_ratings],
            alternative='greater'
        ),
        'value': stats.mannwhitneyu(
            [r['value'] for r in quality_ratings],
            [r['value'] for r in baseline_ratings],
            alternative='greater'
        ),
        'diversity': stats.mannwhitneyu(
            quality_diversity,
            baseline_diversity,
            alternative='greater'
        )
    }

    # Check validation threshold
    significant_dimensions = sum(1 for r in ['insight', 'conversation', 'value']
                                  if results[r].pvalue < 0.05)
    diversity_significant = results['diversity'].pvalue < 0.05

    validation_passed = significant_dimensions >= 2 and diversity_significant

    return {
        'results': results,
        'validation_passed': validation_passed,
        'recommendation': (
            "Proceed with H5" if validation_passed
            else "Revise quality prompt or drop H5"
        )
    }
```
