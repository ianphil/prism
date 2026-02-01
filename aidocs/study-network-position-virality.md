# Study Design: Network Position as Equalizer for Small Accounts

Pre-registration style study design following OSF guidelines.

**Template reference**: https://osf.io/prereg/

**Version**: 2.0 (Revised based on methodological review)

---

## 1. Have any data been collected for this study already?

No simulation data has been collected. However, the Higgs Twitter dataset (SNAP) will be used for validation analysis before running simulations. This validation is exploratory and separate from the confirmatory simulation experiment.

## 2. What's the main question being asked or hypothesis being tested?

**Research Question**: Can network position (bridge vs peripheral) compensate for low follower count in achieving content virality under X's recommendation algorithm?

### Primary Hypothesis (H1) - Equivalence Test

**H1**: Small accounts (≤100 followers) at bridge positions achieve cascade sizes *equivalent to* large accounts (>1000 followers) at peripheral positions, where equivalence is defined as the difference falling within +/-25% of the large-peripheral group mean.

**Equivalence Testing Framework (TOST)**:
- We will use Two One-Sided Tests (TOST) to establish equivalence
- Equivalence margin (delta): +/-25% of Large-Peripheral mean cascade size
- This margin was chosen because: (a) a 25% difference represents a practically meaningful distinction in viral reach, and (b) smaller margins would require infeasibly large sample sizes
- H1 is supported if the 90% confidence interval for the difference (Small-Bridge minus Large-Peripheral) falls entirely within [-delta, +delta]

**Justification for equivalence margin**: In social media contexts, a 25% difference in cascade size (e.g., 1000 vs 1250 reshares) is at the threshold of practical significance. Differences smaller than this are unlikely to affect real-world outcomes (e.g., whether content "goes viral" in popular perception).

### Secondary Hypotheses

- **H2**: Small accounts at peripheral positions achieve significantly smaller cascades than all other conditions. Expected ordering: Large-Bridge > Large-Peripheral approximately equal to Small-Bridge > Small-Peripheral.
- **H3**: The bridge position effect (difference between bridge and peripheral within size category) is larger under X's algorithm (x_algo mode) than under random feed curation.

### Null Hypothesis (H0)

Network position does not moderate the relationship between follower count and cascade size; the difference between Small-Bridge and Large-Peripheral falls outside the equivalence margin.

## 3. Describe the key dependent variable(s)

**Primary DV**: Cascade size (total number of reshares of the seed post, including transitive reshares)

**Secondary DVs**:
| Variable | Definition | Measurement |
|----------|------------|-------------|
| Reach percentage | cascade_size / total_agents | Proportion 0-1 |
| Cascade depth | Maximum hops from seed author | Integer >=0 |
| Time to 10% reach | Rounds until 10% of network reshared | Integer or NA |
| Cross-community spread | Number of distinct communities reached | Integer 1-5 |
| Influencer capture | Whether any large account (>500 followers) reshared | Binary |

**Manipulation Check DV** (see Section 8):
| Variable | Definition | Measurement |
|----------|------------|-------------|
| Cross-community routing | Proportion of cascade paths that cross community boundaries via seed agent | Proportion 0-1 |
| Bridging efficiency | Information flow through seed agent vs alternative paths | Ratio |

## 4. How many and which conditions will participants be assigned to?

**Design**: 2x2 between-subjects factorial

| Factor | Levels | Operationalization |
|--------|--------|-------------------|
| Account size | Small, Large | Small: ≤100 followers; Large: >1000 followers |
| Network position | Bridge, Peripheral | Bridge: top 10% betweenness centrality; Peripheral: bottom 50% |

**Conditions**:
| Condition | Size | Position | Role |
|-----------|------|----------|------|
| A | Large | Bridge | Baseline (expected highest) |
| B | Large | Peripheral | Size advantage only |
| C | Small | Bridge | **Key test condition** |
| D | Small | Peripheral | Expected lowest |

### Justification for Percentile Thresholds

**Bridge (top 10% betweenness)**:
- Theoretical basis: Bridge nodes are structurally rare in social networks; selecting the top decile ensures we capture nodes that genuinely connect otherwise separate clusters
- Empirical support: Analysis of the Higgs dataset shows that the top 10% of nodes by betweenness centrality account for >60% of cross-community information flow
- The sharp threshold avoids ambiguous cases where structural bridging is uncertain

**Peripheral (bottom 50% betweenness)**:
- Theoretical basis: Peripheral nodes are common by definition; the median provides a natural cutoff
- The 50th percentile ensures sufficient eligible agents while excluding the "middle" range (50th-90th percentile) where bridging function is ambiguous
- Excluding the middle range creates cleaner experimental contrast and avoids misclassification

**Gap justification**: The 40-percentile gap between conditions is intentional to maximize contrast. Agents in the 50th-90th percentile range have intermediate bridging capacity that would dilute the experimental manipulation. Including them would test a weaker version of the hypothesis.

**Fixed parameters**:
- Agents: 500
- Rounds: 50
- Feed mode: x_algo (primary), random (secondary comparison)
- Network topology: Stochastic block model (5 communities)
- Seed post: Identical text content across all conditions

### Network Parameters (Aligned with Study 2)

```yaml
network:
  topology: "stochastic_block"
  stochastic_block:
    communities: 5
    agents_per_community: 100
    p_within: 0.12        # Aligned between studies (midpoint)
    p_between: 0.008      # Aligned between studies (midpoint)
  seed: 42  # Fixed across all conditions
```

**Rationale for alignment**: Studies 1 and 2 use identical network parameters to ensure that bridge position value established in Study 1 transfers to Study 2's growth context. The midpoint values (p_within=0.12, p_between=0.008) balance between Study 1's need for sufficient cascade potential and Study 2's need for growth room.

## 5. Specify exactly which analyses you will conduct

### Feasibility Check (Pre-Simulation)

Before running the experiment, generate 10 networks with the specified parameters and report:
1. **Eligible agent counts** per condition (must have >=50 eligible agents per cell to proceed)
2. **Follower-betweenness correlation** (Spearman's rho) - will be reported to characterize confounding
3. **Expected cell characteristics** - mean/SD of followers and betweenness within each eligible pool

If any cell has <50 eligible agents, the network parameters will be adjusted (increasing p_between to create more bridge opportunities) and the feasibility check repeated.

### Primary Analysis: Equivalence Test (TOST)

**Procedure**:
1. Calculate mean cascade size for Large-Peripheral condition (M_LP)
2. Define equivalence margin: delta = 0.25 x M_LP
3. Conduct Two One-Sided Tests:
   - Test 1 (non-inferiority): H0: mu_SB - mu_LP <= -delta vs H1: mu_SB - mu_LP > -delta
   - Test 2 (non-superiority): H0: mu_SB - mu_LP >= delta vs H1: mu_SB - mu_LP < delta
4. Use Wilcoxon-Mann-Whitney tests for each one-sided comparison (non-parametric)
5. Equivalence is established if both tests reject at alpha = 0.05

**Decision rule**:
- If TOST p < 0.05: Conclude equivalence (H1 supported)
- If TOST p >= 0.05: Cannot conclude equivalence (H1 not supported)

**Reporting**: Report the 90% CI for the difference and visualize against equivalence bounds.

### Secondary Analysis: Omnibus Test

**Test**: Kruskal-Wallis H-test across all four conditions on cascade size
- Non-parametric (cascade sizes likely non-normal)
- alpha = 0.05

**Post-hoc**: Dunn's test with Bonferroni correction for pairwise comparisons

### Interaction Analysis: Aligned Rank Transform (ART) ANOVA

To test for Size x Position interaction while respecting non-normal distributions:

**Procedure**:
1. Apply Aligned Rank Transform to cascade size data (Wobbrock et al., 2011)
2. Conduct 2x2 factorial ANOVA on ART data
3. Report main effects (Size, Position) and interaction (Size x Position)
4. Significant interaction (p < 0.05) supports the moderation hypothesis

**Software**: R package `ARTool` or Python implementation

**Rationale**: ART-ANOVA properly handles interaction effects in non-parametric factorial designs, unlike simple rank transformation which can inflate or mask interactions.

### Effect Sizes

- **Equivalence test**: Report Cohen's d and 90% CI for Small-Bridge vs Large-Peripheral
- **Omnibus**: Report epsilon-squared for Kruskal-Wallis
- **Pairwise**: Report rank-biserial correlation (r) for each Mann-Whitney comparison
- Interpretation: |r| < 0.3 small, 0.3-0.5 medium, >0.5 large

### Feed Mode Comparison (H3)

- Repeat primary analysis under random feed mode
- Compare effect sizes between x_algo and random
- Use bootstrap to construct CI for the difference in effect sizes

### Exploratory Analyses

- Correlation: betweenness centrality x cascade size (continuous, Spearman's rho)
- Pathway analysis: Did small-bridge cascades route through influencers?
- Time-series: Cascade growth curves by condition

## 6. Describe exactly how outliers will be defined and handled

**Outlier definition**: Cascade sizes beyond 3x IQR from median within each condition.

**Handling**:
1. Primary analysis includes all data (intent-to-treat principle)
2. Sensitivity analysis excludes outliers to check robustness
3. Report both results; conclusions based on primary analysis

**Failed simulations**: Runs where seed post receives zero engagement after round 1 are excluded (simulation failure, not valid data point). Expected rate: <5%.

## 7. How many observations will be collected or what will determine sample size?

**Replications per condition**: 50 (increased from 30 for equivalence testing power)

**Total simulation runs**: 4 conditions x 50 replications = 200 runs

**Justification**:

*For equivalence testing*: Power analysis for TOST with:
- Equivalence margin: delta = 0.25 (standardized, assuming SD approximately equal to mean)
- Expected true difference: 0 (under H1)
- alpha = 0.05 (one-sided tests), power = 0.80
- Required n per group: ~45
- We round to 50 for robustness

*Comparison to prior work*: Ferraro et al. (2024) used 10 iterations; we increase substantially for equivalence testing requirements.

**Computational estimate**: 200 runs x ~2.5 hrs = ~500 hrs total (parallelizable to ~21 hrs with 24 cores)

**Stopping rule**: All 200 runs complete. No early stopping or peeking at results.

## 8. Anything else you would like to pre-register?

### Manipulation Check: Bridge Function Verification

To verify that structural bridge position translates to functional bridging behavior, we will assess whether bridge-position seed agents actually facilitate cross-community information flow.

**Manipulation check procedure**:

```python
def verify_bridge_function(cascade, seed_agent, communities):
    """
    Check that bridge agents actually route information across communities.
    Returns metrics indicating functional bridging.
    """
    # 1. Count communities reached in cascade
    communities_reached = set()
    for node in cascade.nodes:
        communities_reached.add(get_community(node))

    # 2. Calculate cross-community routing through seed
    # A path "routes through seed" if it goes:
    # community_A -> seed -> community_B (where A != B)
    cross_community_paths = 0
    total_paths = 0

    for path in cascade.all_paths_from_seed():
        if len(path) >= 2:
            total_paths += 1
            source_community = get_community(path[0])
            dest_community = get_community(path[-1])
            if source_community != dest_community:
                cross_community_paths += 1

    routing_ratio = cross_community_paths / total_paths if total_paths > 0 else 0

    # 3. Bridging efficiency: compare to counterfactual
    # Would information have spread across communities without this agent?
    efficiency = calculate_bridging_efficiency(cascade, seed_agent)

    return {
        'communities_reached': len(communities_reached),
        'cross_community_routing_ratio': routing_ratio,
        'bridging_efficiency': efficiency
    }
```

**Expected results**:
- Bridge-position agents should show higher cross-community routing ratio than peripheral agents
- If bridge agents do not show higher routing ratios, the structural-functional link is not supported

**Decision rule**: If mean routing ratio for bridge conditions is not significantly higher (p < 0.05, one-tailed) than peripheral conditions, we will report this as a manipulation failure and interpret cascade results cautiously.

### Agent Selection Criteria

For each condition, eligible seed agents must:
1. Meet follower count criteria (small <=100, large >1000)
2. Meet betweenness criteria (bridge >=90th percentile, peripheral <=50th percentile)
3. **New**: Be matched on community membership across conditions within each replication

**Stratified selection procedure**:
```python
def select_matched_agents(network, n_replications=50):
    """
    Select seed agents matched on community to reduce confounding.
    """
    selections = []

    for rep in range(n_replications):
        # For each community, find eligible agents for each condition
        for community_id in range(5):
            community_agents = get_agents_in_community(community_id)

            eligible = {
                'large_bridge': filter_eligible(community_agents,
                    followers='>1000', betweenness='>=p90'),
                'large_peripheral': filter_eligible(community_agents,
                    followers='>1000', betweenness='<=p50'),
                'small_bridge': filter_eligible(community_agents,
                    followers='<=100', betweenness='>=p90'),
                'small_peripheral': filter_eligible(community_agents,
                    followers='<=100', betweenness='<=p50'),
            }

            # Randomly select one agent per condition from this community
            # This ensures community is balanced across conditions
            for condition, pool in eligible.items():
                if pool:
                    selected = random.choice(pool)
                    selections.append({
                        'replication': rep,
                        'community': community_id,
                        'condition': condition,
                        'agent_id': selected
                    })

    return selections
```

### Seed Post Content

Identical across all conditions:
```
Just mass adoption starting? My local coffee shop now accepts Bitcoin!
```
- No media attachment (has_media: false)
- Neutral topic (crypto/tech) matching agent interest distribution

**Limitation acknowledged**: Results may be content-specific. Future studies should test generalization across topics (tech, sports, politics, entertainment).

### Validation Phase (Pre-Simulation)

Before running simulations, analyze Higgs dataset:
1. Calculate betweenness centrality and follower counts
2. Correlate with real cascade sizes for small accounts
3. **Decision gate**:
   - If Spearman's rho (betweenness x cascade) < 0.15 for small accounts, revise hypothesis
   - Revision options: (a) adjust betweenness threshold, (b) consider alternative centrality measures, (c) document as exploratory

This validation is exploratory and does not affect the confirmatory simulation design, but informs interpretation.

### Reporting Follower-Betweenness Confounding

We will report:
1. Spearman correlation between follower count and betweenness centrality in the generated network
2. Distribution of followers within each betweenness category (bridge, peripheral)
3. Any agents that were excluded due to conflicting criteria (high followers + peripheral, or low followers + bridge)

This transparency allows readers to assess the severity of natural confounding.

### Criteria for Proceeding to Study 2

Study 2 (Growth Strategies) should only proceed if Study 1 provides evidence that bridge position is valuable. Quantitative criteria:

**Proceed to Study 2 if ANY of the following are met**:
1. **Equivalence established**: TOST shows Small-Bridge approximately equal to Large-Peripheral (p < 0.05)
2. **Bridge effect significant**: Bridge positions show significantly larger cascades than peripheral positions (main effect in ART-ANOVA, p < 0.05, epsilon-squared > 0.06)
3. **Correlation threshold**: Spearman's rho (betweenness x cascade size) > 0.25 across all agents

**Do not proceed if**:
- Bridge position shows no advantage (main effect p > 0.10)
- AND follower count entirely dominates (size main effect epsilon-squared > 0.20, position epsilon-squared < 0.02)

If results are ambiguous (e.g., marginal effects), document uncertainty and proceed with Study 2 as exploratory.

## 9. Type of study and samples

**Study type**: Computational simulation experiment

**Sample**:
- 500 LLM-driven agents per simulation
- Agents initialized with profiles derived from Twitter data (interests, personality)
- Network topology generated via stochastic block model

**Platform simulated**: X (Twitter) recommendation algorithm based on open-sourced code

**Version control**: X algorithm simulation will use commit hash [to be specified before data collection] from the public repository.

---

## References

- Ferraro, F., et al. (2024). Agent-Based Modelling Meets Generative AI in Social Network Simulations. arXiv:2411.16031
- De Domenico, M., et al. (2013). Anatomy of a scientific rumor. Scientific Reports. (Higgs dataset)
- X Algorithm: https://github.com/twitter/the-algorithm
- Wobbrock, J. O., et al. (2011). The Aligned Rank Transform for nonparametric factorial analyses. CHI 2011.
- Lakens, D. (2017). Equivalence tests: A practical primer. Social Psychological and Personality Science.
- Schuirmann, D. J. (1987). A comparison of the two one-sided tests procedure and the power approach for assessing equivalence. Journal of Pharmacokinetics.

## Appendix A: Variable Operationalization

### Betweenness Centrality

```python
import networkx as nx

G = social_graph  # Directed follow graph
betweenness = nx.betweenness_centrality(G, normalized=True)

# Classification thresholds
bridge_threshold = np.percentile(list(betweenness.values()), 90)
peripheral_threshold = np.percentile(list(betweenness.values()), 50)

def classify_position(agent_id):
    score = betweenness[agent_id]
    if score >= bridge_threshold:
        return "bridge"
    elif score <= peripheral_threshold:
        return "peripheral"
    else:
        return "middle"  # Excluded from experiment
```

### Cascade Size Measurement

```python
def measure_cascade(simulation_result, seed_post_id):
    reshares = [
        action for action in simulation_result.actions
        if action.type == "RESHARE" and action.target_post_id == seed_post_id
    ]
    # Include transitive reshares (reshares of reshares)
    cascade = build_cascade_tree(seed_post_id, simulation_result)
    return len(cascade.nodes)
```

## Appendix B: TOST Equivalence Test Implementation

```python
from scipy import stats
import numpy as np

def tost_equivalence_test(group1, group2, margin_proportion=0.25):
    """
    Two One-Sided Tests for equivalence.

    Args:
        group1: Small-Bridge cascade sizes
        group2: Large-Peripheral cascade sizes
        margin_proportion: Equivalence margin as proportion of group2 mean

    Returns:
        dict with test results and interpretation
    """
    # Calculate equivalence margin based on group2 (Large-Peripheral)
    margin = margin_proportion * np.mean(group2)

    # Difference (group1 - group2)
    diff = np.mean(group1) - np.mean(group2)

    # Non-parametric: use Wilcoxon rank-sum (Mann-Whitney) for each direction
    # Test 1: Is group1 not substantially worse than group2?
    # H0: mu1 - mu2 <= -margin (group1 is worse by at least margin)
    # We test if group1 - (-margin) > group2, i.e., group1 + margin > group2
    shifted_group1_lower = group1 + margin
    stat1, p1 = stats.mannwhitneyu(shifted_group1_lower, group2, alternative='greater')

    # Test 2: Is group1 not substantially better than group2?
    # H0: mu1 - mu2 >= margin (group1 is better by at least margin)
    # We test if group1 - margin < group2, i.e., group1 < group2 + margin
    shifted_group2_upper = group2 + margin
    stat2, p2 = stats.mannwhitneyu(group1, shifted_group2_upper, alternative='less')

    # TOST conclusion: reject both null hypotheses
    tost_p = max(p1, p2)  # Both must be significant
    equivalence_established = tost_p < 0.05

    # Calculate 90% CI for difference (for visualization)
    # Using bootstrap for non-parametric CI
    bootstrap_diffs = []
    for _ in range(10000):
        b1 = np.random.choice(group1, size=len(group1), replace=True)
        b2 = np.random.choice(group2, size=len(group2), replace=True)
        bootstrap_diffs.append(np.mean(b1) - np.mean(b2))
    ci_lower = np.percentile(bootstrap_diffs, 5)
    ci_upper = np.percentile(bootstrap_diffs, 95)

    return {
        'equivalence_margin': margin,
        'observed_difference': diff,
        'ci_90': (ci_lower, ci_upper),
        'p_lower': p1,
        'p_upper': p2,
        'tost_p': tost_p,
        'equivalence_established': equivalence_established,
        'interpretation': (
            f"90% CI [{ci_lower:.1f}, {ci_upper:.1f}] "
            f"{'falls within' if equivalence_established else 'extends beyond'} "
            f"equivalence bounds [-{margin:.1f}, +{margin:.1f}]"
        )
    }
```

## Appendix C: Feasibility Check Protocol

```python
def conduct_feasibility_check(n_networks=10):
    """
    Generate networks and verify sufficient agents exist for each condition.
    Must be run before main experiment.
    """
    results = {
        'eligible_counts': [],
        'follower_betweenness_correlations': [],
        'cell_characteristics': []
    }

    for seed in range(n_networks):
        network = generate_stochastic_block_network(
            communities=5,
            agents_per_community=100,
            p_within=0.12,
            p_between=0.008,
            seed=seed
        )

        # Calculate metrics
        betweenness = nx.betweenness_centrality(network, normalized=True)
        followers = {n: network.in_degree(n) for n in network.nodes()}

        # Classify agents
        bridge_thresh = np.percentile(list(betweenness.values()), 90)
        periph_thresh = np.percentile(list(betweenness.values()), 50)

        eligible = {
            'large_bridge': [],
            'large_peripheral': [],
            'small_bridge': [],
            'small_peripheral': []
        }

        for agent in network.nodes():
            f = followers[agent]
            b = betweenness[agent]

            is_large = f > 1000
            is_small = f <= 100
            is_bridge = b >= bridge_thresh
            is_peripheral = b <= periph_thresh

            if is_large and is_bridge:
                eligible['large_bridge'].append(agent)
            elif is_large and is_peripheral:
                eligible['large_peripheral'].append(agent)
            elif is_small and is_bridge:
                eligible['small_bridge'].append(agent)
            elif is_small and is_peripheral:
                eligible['small_peripheral'].append(agent)

        results['eligible_counts'].append({
            k: len(v) for k, v in eligible.items()
        })

        # Correlation
        f_list = list(followers.values())
        b_list = [betweenness[n] for n in followers.keys()]
        rho, p = stats.spearmanr(f_list, b_list)
        results['follower_betweenness_correlations'].append(rho)

    # Summarize
    print("=== Feasibility Check Results ===")
    for condition in eligible.keys():
        counts = [r[condition] for r in results['eligible_counts']]
        print(f"{condition}: mean={np.mean(counts):.1f}, min={min(counts)}, max={max(counts)}")

    print(f"\nFollower-Betweenness correlation: "
          f"mean rho = {np.mean(results['follower_betweenness_correlations']):.3f}")

    # Check proceed criteria
    min_eligible = min(
        min(r[c] for r in results['eligible_counts'])
        for c in eligible.keys()
    )

    if min_eligible < 50:
        print(f"\nFEASIBILITY FAILED: Minimum eligible count ({min_eligible}) < 50")
        print("Recommendation: Increase p_between or adjust follower thresholds")
    else:
        print(f"\nFEASIBILITY PASSED: All cells have >={min_eligible} eligible agents")

    return results
```
