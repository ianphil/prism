---
target:
  - configs/default.yaml
  - main.py
  - prism/agents/social_agent.py
  - prism/agents/prompts.py
  - prism/llm/config.py
  - prism/metrics/cascades.py
  - prism/metrics/virality.py
  - prism/experiments/runner.py
---

# PRISM Study-Level Intent

Validates that PRISM delivers on its core research purpose: a generative agent-based simulator that enables controlled experiments on information spread and content virality. 

## Simulation Apparatus

### Config-driven simulations with reproducible parameters

Researchers must reproduce exact simulation conditions across runs. Without config-driven reproducibility, no experimental result is trustworthy and no peer review is possible. Discounting the stochastic nature of LLMs.

```
Given the configs/default.yaml file and the prism/llm/config.py file
When examining the configuration system
Then simulation parameters (model, temperature, seed, agent count, round count) are specified in config files
And a seed value can be set for deterministic behavior
And changing config values does not require code changes
```

### Agents have distinct profiles that shape behavior

If all 500 agents behave identically, the simulation produces no meaningful emergent behavior. Profile-driven diversity is the foundation of realistic social dynamics — homophily, polarization, and cascade patterns all depend on agents having different interests and personalities.

```
Given the prism/agents/social_agent.py and prism/agents/prompts.py files
When examining how agent profiles influence decisions
Then each agent is constructed with distinct profile data (interests, personality, or similar)
And the agent's profile is injected into the LLM prompt
And agents with different profiles can produce different decisions for the same feed
```

### Agents produce structured social media decisions

Downstream analysis (cascade tracking, engagement metrics, virality measurement) requires machine-parseable decisions — not free-text LLM output. If decisions aren't structured, no metric pipeline can consume them.

```
Given the prism/agents/social_agent.py file
When examining the agent decision flow
Then agents output structured decisions with a choice (LIKE, REPLY, RESHARE, SCROLL), a reason, and optional content
And the decision is a validated data model, not a raw string or dict
```

### Cascade metrics can be measured from simulation output

The entire research value of PRISM depends on measuring how information spreads. Without cascade tracking (size, depth, breadth), the system is an agent chatbot, not a research tool.

```
Given the prism/metrics/cascades.py file
When examining cascade measurement capabilities
Then the system tracks reshare chains as graph structures
And it can compute cascade size (total reshares), depth (longest chain), and breadth (max width at any level)
And metrics are computable from simulation output without manual intervention
```

### Simulation runs locally without cloud dependencies

Cloud API costs make large-scale experiments (20-50 replications x 250-500 agents x 50 rounds) financially impractical. Local-first inference via Ollama is a hard requirement for the research to be viable.

```
Given the configs/default.yaml and prism/llm/config.py files
When examining the default LLM configuration
Then the default configuration targets a local Ollama instance
And no cloud API keys or external service credentials are required to run a simulation
```

## Experimental Apparatus

### System supports controlled experiment design with treatment and control conditions

Without controlled experiments, PRISM cannot test any hypothesis. The system must support defining paired conditions (treatment vs control) that isolate a single independent variable.

```
Given the prism/experiments/runner.py file
When examining experiment execution capabilities
Then experiments can define multiple conditions (e.g., treatment and control)
And each condition can be run with the same agent pool and configuration except for the manipulated variable
And multiple replications can be executed per condition for statistical validity
```

### Feed mode is configurable between algorithmic and random

The PRD's core experiment compares algorithmic curation (preference-based or X-algo) against random feeds. If feed mode isn't a toggleable parameter, the primary experimental variable cannot be manipulated.

```
Given the configs/default.yaml file or experiment configuration
When examining feed configuration options
Then the system supports at least two feed modes: preference-based (or algorithmic) and random
And the feed mode can be set via configuration without code changes
```

## Visuals-Drive-Virality Hypothesis

### Posts carry media metadata flags for experimental manipulation

The PRD's primary hypothesis tests whether visual content drives larger cascades. Posts must carry a has_media flag and media description — this is the independent variable. Without it, the hypothesis cannot be expressed in the system.

```
Given the post data model in the codebase
When examining post structure
Then posts have a media presence flag (has_media or similar boolean)
And posts have a media type field (image, video, gif, or similar)
And posts have a media description field for textual representation of visual content
```

### Media metadata is presented to agents in feed prompts

Agents must perceive which posts have visual content to make differential decisions. If media flags exist in data but aren't surfaced in the prompt, agents can't distinguish treatment from control posts.

```
Given the prism/agents/prompts.py file
When examining how posts with media are formatted for agents
Then posts with media include a visual indicator or description in the prompt text
And the presentation distinguishes media posts from text-only posts
```

### Experiment config can express the 2x2 visuals study design

The PRD specifies a 2x2 factorial design: visuals (yes/no) x feed mode (algorithmic/random). If this design can't be expressed in config, researchers must hardcode experiment conditions — breaking reproducibility and peer review.

```
Given the experiment configuration system
When examining how the visuals hypothesis study is defined
Then the configuration can express paired conditions: posts with media vs posts without media
And the configuration can express feed mode as a second factor (algorithmic vs random)
And the design supports replication counts per condition
```

### Cascade comparison between conditions is measurable

The hypothesis predicts at least 2x cascade size for visual posts. The system must produce per-condition cascade metrics that can be compared statistically. Without this, the experiment runs but produces no testable result.

```
Given the prism/metrics/cascades.py or prism/metrics/virality.py file
When examining how cascade metrics are reported
Then cascade metrics (size, depth) can be computed per experimental condition
And results from different conditions can be compared (e.g., treatment vs control cascade sizes)
And the output supports statistical comparison (provides per-replication values, not just aggregates)
```
