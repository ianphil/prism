# Product Requirements Document (PRD): PRISM

## Platform Replication for Information Spread Modeling

*A Generative Agent-Based Social Media Simulator*

## Version History
- **Version**: 1.3
- **Date**: January 31, 2026
- **Author**: Grok 4 (xAI), revised with Claude (Anthropic)
- **Status**: Draft
- **Changes from v1.2**:
  - **Updated research focus** from "visuals drive virality" to network position studies
  - Added two pre-registered studies (see `aidocs/study-*.md`):
    - Study 1: Network position as equalizer for small accounts
    - Study 2: Growth strategies for follower acquisition
  - Studies use OSF pre-registration format with TOST equivalence testing
  - Added dynamic network capability requirements for Study 2
  - X algorithm integration now supports in-network vs out-of-network analysis

- **Version**: 1.2
- **Date**: January 27, 2026
- **Changes from v1.1**:
  - Replaced PyAutoGen with Microsoft Agent Framework as the core orchestration layer
  - Updated technical architecture to leverage Agent Framework's graph-based workflows, IChatClient abstraction, and observability features
  - **Selected gpt-oss:20b as primary LLM** based on M3 Ultra benchmarks showing significantly better agent reasoning quality vs Mistral 7B (human-like responses vs bot-like), accepting 4x speed trade-off for research validity
  - Revised agent targets from 1000 to 250-500 based on gpt-oss:20b inference times (~3.1s vs ~0.8s for Mistral)
  - Added detailed performance benchmarks from actual M3 Ultra testing
  - Updated timeline to reflect new framework integration

## Executive Summary

### Problem Statement
Social media phenomena like virality are driven by complex interactions between users, content, and algorithms. Traditional simulations lack realism in human-like decision-making and algorithmic personalization. This system addresses this by combining generative agents (LLM-driven) with RAG-based feed simulation and integrations with X's open-sourced recommendation algorithm, allowing controlled experiments on "why" content goes viral (e.g., role of preferences, early engagement, network effects).

### Objective
Build PRISM, a Python-based toolkit for running generative agent-based simulations of Twitter/X-like platforms. Key goals:
- Replicate emergent behaviors (e.g., cascades, homophily) grounded in real data.
- Incorporate X's recommendation algorithm for realistic feed curation.
- Enable easy experimentation (e.g., A/B testing preference-based vs. random feeds).
- Support studies on virality metrics (e.g., cascade size, retweet depth).
- Run efficiently on local hardware (M3 Ultra Mac Studio) using Ollama with gpt-oss:20b for high-quality agent reasoning.

### Target Users
- Researchers in social sciences, AI, or computational sociology.
- Developers building agentic AI tools.
- Platform designers testing algorithm impacts.

### Key Benefits
- **Quality-first**: gpt-oss:20b provides human-like agent reasoning for realistic social simulation.
- **Local-first**: Full simulation runs on consumer hardware via Ollama, no cloud API costs.
- **Modular**: Swap LLM providers (Ollama, Azure, OpenAI) via IChatClient abstraction.
- **Observable**: Built-in OpenTelemetry integration for tracing, debugging, and experiment analysis.
- **Scalable**: Target 250-500 agents for experiments; 100 agents for rapid development iteration.
- **Reproducible**: Config-driven simulations with checkpointing and logging for validation.

## Scope

### In Scope
- Core simulation loop: Agent decision-making, interactions, and logging via Microsoft Agent Framework.
- RAG-based feed simulation with preference/random modes using ChromaDB.
- Integration of X's open-sourced recommendation algorithm (candidate sourcing, ranking).
- Data ingestion/validation from real Twitter datasets.
- Metrics tracking for virality (e.g., cascade size, depth, resharing rates).
- CLI for running experiments and visualizing results.
- Framework for hypothesis-driven studies, including phased testing plans (e.g., A/B MVP to DOE).
- Local LLM inference via Ollama on M3 Ultra Mac Studio.

### Out of Scope (Phase 1)
- Full-scale production deployment (e.g., cloud orchestration for 10K+ agents).
- Real-time web scraping (use pre-loaded datasets).
- Advanced ML training (e.g., fine-tuning LLMs on custom data).
- Mobile/web frontend (focus on CLI/Python scripts).

### Assumptions
- Primary development target: M3 Ultra Mac Studio with 512GB unified memory.
- gpt-oss:20b provides sufficient reasoning quality for realistic social agent behavior (~3s/inference).
- 250-500 agent simulations complete in reasonable timeframes with Ollama parallelization.
- Microsoft Agent Framework Python packages remain stable through preview period.
- X's algo repo provides sufficient details for porting key ranking heuristics.
- Ethical use: Simulations for research only, no real-user data without consent.

### Risks and Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM throughput bottleneck | Simulation runtime too long | Use Mistral 7B for development; parallelize Ollama; tune reasoning effort |
| Agent reasoning quality | Unrealistic emergent behavior | Use gpt-oss:20b for experiments; validate against real social data |
| Agent Framework Python immaturity | API changes, missing features | Pin versions, maintain abstraction layer, fallback to direct Ollama calls |
| Algo Changes | X's open-source may evolve | Modular wrappers, version-lock reference implementation |
| Data Bias | Real datasets skew results | Configurable preprocessing, synthetic agent generation option |
| Memory pressure | OOM on simulation state | Streaming inference, lazy loading of agent context, sampling in RAG |

## Functional Requirements

### Core Components

#### 1. Agent Framework Integration
- Use Microsoft Agent Framework (Python) as the orchestration layer.
- Leverage `IChatClient` abstraction for LLM provider flexibility.
- Each social media agent implemented as a `ChatAgent` with:
  - Personality/interests inferred from real Twitter data
  - System prompt defining decision-making behavior
  - Tool access for RAG feed retrieval
- Agent decisions output as structured Choice-Reason-Content triplets.
- Prompt template includes: profile traits, RAG-retrieved feed, action constraints, media flags.

```python
# Conceptual agent setup
from agent_framework import ChatAgent
from agent_framework.ollama import OllamaChatClient

agent = ChatAgent(
    chat_client=OllamaChatClient(
        endpoint="http://localhost:11434",
        model="gpt-oss:20b"
    ),
    name=f"agent_{user_id}",
    instructions=build_agent_prompt(profile, interests, personality)
)
```

#### 2. Simulation Orchestration
- Graph-based workflow connecting:
  - Feed retrieval (RAG query per agent)
  - Agent decision (LLM inference)
  - Action application (state update)
  - Logging (metrics, traces)
- Support for checkpointing and replay (time-travel debugging).
- Configurable parallelism for agent batching.
- Round-robin iterations: 50-100 rounds, 250-500 agents target for experiments.

```python
# Conceptual workflow structure
from agent_framework.workflows import Workflow, Edge

workflow = Workflow()
workflow.add_executor("feed_retrieval", feed_retriever)
workflow.add_executor("agent_decision", agent_pool)
workflow.add_executor("state_update", state_manager)
workflow.add_executor("logging", metrics_logger)

workflow.add_edge(Edge("feed_retrieval", "agent_decision"))
workflow.add_edge(Edge("agent_decision", "state_update"))
workflow.add_edge(Edge("state_update", "logging"))
```

#### 3. Local LLM Provider (Ollama)
- Primary inference via Ollama running on M3 Ultra.
- **Primary model: gpt-oss:20b** (OpenAI's open-weight model)
  
**Why gpt-oss:20b over smaller models:**

Benchmark testing on M3 Ultra (512GB) compared gpt-oss:20b against Mistral 7B using a representative agent decision prompt. While both models achieved similar token generation rates (~104 tok/s), the quality difference is significant for social simulation:

| Aspect | Mistral 7B | gpt-oss:20b |
|--------|------------|-------------|
| Response time | ~0.8s | ~3.1s |
| Decision quality | Generic reasoning | Nuanced, contextual |
| Content realism | Bot-like (hashtag stuffing, repetition) | Human-like (conversational, asks questions) |
| Engagement style | Passive amplification | Active conversation starter |

Example output comparison for the same crypto-related post:
- **Mistral**: Chose RESHARE with generic content: "My local coffee shop now accepts Bitcoin payments! The future is here! #BitcoinAdoption #Cryptocurrency #TechStartups"
- **gpt-oss:20b**: Chose REPLY with engaging content: "Awesome news! 👏 Have you guys tried tipping with Bitcoin? Any feedback on the payment experience so far? 🚀"

For a virality simulation studying cascade dynamics and emergent behavior, agent reasoning quality directly impacts:
1. **Cascade realism** — REPLY vs RESHARE decisions create different network patterns
2. **Content diversity** — Rich generated content vs repetitive amplification
3. **Emergent phenomena** — The core value of GABM requires human-like agent behavior

The 4x speed penalty is acceptable given the quality improvement for research validity.

**Model specifications:**
- **gpt-oss:20b**: 21B params (3.6B active MoE), 14GB VRAM, 128K context, native tool calling, Apache 2.0
- Configurable reasoning effort (low/medium/high) via system prompt for speed/quality tuning
- Native structured outputs and function calling support

**Secondary models (for development/hybrid approaches):**
- **Mistral 7B**: Fast iteration during development (~0.8s/inference)
- **Phi-3/Phi-4**: Lightweight triage decisions if hybrid approach needed

- Configuration for parallel Ollama instances to maximize throughput.
- Fallback support for Azure OpenAI / OpenAI via same IChatClient interface.

#### 4. Memory and RAG System
- ChromaDB as vector store for posts, actions, and embeddings.
- Embeddings via sentence-transformers (local) or Ollama embedding models.
- RAG Loop per agent turn:
  - Retrieve 5-10 candidate posts based on mode.
  - **Preference-based**: Cosine similarity on agent interests + X algo scoring.
  - **Random**: Uniform sampling from recent posts.
- Storage: Embed and index all generated content for future retrievals.

#### 5. Recommendation Algorithm Integration
- Port key elements from X's open-sourced recommendation system:
  - **Candidate Sourcing**: In-network (followed agents) + out-of-network (embedding similarity).
  - **Ranking**: Lightweight scoring for engagement prediction + heuristics (velocity, media boost).
- Implementation options:
  - Pure Python reimplementation of core heuristics.
  - LLM-based ranking via secondary prompt (use X-inspired features as context).
- Configurable: Toggle full X mode, simplified preference, or custom hybrids.

#### 6. Data Pipeline
- **Ingestion**: Load real Twitter datasets (CSV/JSON of tweets/users).
- **Preprocessing**: 
  - Filter bots (Botometer scores if available).
  - Infer traits via KeyBERT/YAKE for interests, BERT classifier for political stance.
  - Generate agent profiles from user metadata.
- **Validation**: Post-sim checks (linguistic similarity, homophily metrics via NetworkX).

#### 7. Observability and Analytics
- **OpenTelemetry Integration**: Built-in via Agent Framework.
  - Trace every agent decision, tool call, and state transition.
  - Export to Jaeger/Zipkin for visualization during development.
  - Aggregate metrics for experiment analysis.
- **Metrics**: 
  - Cascade size/depth, resharing rates, homophily (assortativity).
  - Per-round engagement rates, content velocity.
  - Virality threshold detection (time-to-N-reshares).
- **Visualization**: Pandas for stats, Matplotlib/NetworkX for cascade graphs.
- **Export**: JSON/CSV for external analysis, pyDOE/SALib integration for DOE.

## Example Studies and Experimentation Framework

### Sample Hypothesis: Visuals Drive Virality
- **Hypothesis Statement**: Posts with visuals (simulated media flags) will generate larger/deeper cascades (≥2x) than text-only posts, especially under algorithmic boosts.
- **Rationale**: Tests how visual content enhances engagement and spread per X's documented media heuristics.
- **Key Variables**:
  - Independent: Visuals (yes/no), Feed Mode (random vs. preference/X-algo).
  - Dependent: Cascade size, depth, resharing rate, time-to-virality.
- **Fixed Parameters**: 250 agents (or 500 for full experiments), 50 rounds, seed with neutral/controversial post, tech/crypto niche profiles.

### Visual Content Simulation Design

**Design Decision: Metadata Simulation over Multimodal**

We simulate visual content via metadata flags and descriptions rather than processing actual images. This approach was chosen for the following reasons:

1. **Matches real platform mechanics.** X's algorithm applies a ~10x boost for posts with native media — this is a metadata flag, not image analysis. Our simulation models the same mechanism that drives real-world virality.

2. **Isolates the experimental variable.** Using actual images would conflate "has image" with "what's in the image." Metadata simulation lets us control content while varying only the media presence flag.

3. **Tests agent decision-making.** The hypothesis is about whether agents *decide* to engage more with visual posts. The prompt tells them "this post has an image of X" — their reasoning about that decision is what we're measuring, not their ability to see images.

4. **Practical efficiency.** gpt-oss:20b excels at text reasoning but doesn't support vision. Avoiding multimodal models keeps inference fast and the RAG system simple.

**Post Data Structure:**

```python
@dataclass
class Post:
    id: str
    author_id: str
    text: str
    timestamp: datetime
    
    # Media simulation
    has_media: bool = False
    media_type: Optional[str] = None  # "image", "video", "gif"
    media_description: Optional[str] = None  # "Photo of...", "Screenshot showing..."
    
    # Engagement metrics (evolve during simulation)
    likes: int = 0
    reshares: int = 0
    replies: int = 0
    
    # For X algorithm ranking
    velocity: float = 0.0  # Engagement rate over time
```

**Feed Presentation to Agents:**

Posts are rendered in the agent's prompt with visual indicators:

```
Post #1:
"Just mass adoption starting? My local coffee shop now accepts Bitcoin!"
[📷 IMAGE: Photo of a coffee shop counter with a Bitcoin payment terminal]
❤️ 89 | 🔁 34 | 💬 12 | 3h ago

Post #2:
"My local coffee shop now accepts Bitcoin payments. The future is here."
❤️ 23 | 🔁 8 | 💬 3 | 3h ago
```

The `[📷 IMAGE: description]` block signals visual content to the agent. The agent's system prompt explains that posts with images tend to be more eye-catching, mirroring real user perception.

**Controlled Comparison Design:**

To isolate the media variable, experiments use paired posts with identical or equivalent text content:

| Condition | Text | Media | Expected Behavior |
|-----------|------|-------|-------------------|
| A (control) | "Coffee shop accepts Bitcoin" | None | Baseline engagement |
| B (treatment) | "Coffee shop accepts Bitcoin" | [IMAGE: Bitcoin terminal photo] | Higher engagement if hypothesis holds |

**X Algorithm Media Boost:**

When feed_mode is set to "x_algo", the ranking score includes a media multiplier:

```python
def calculate_ranking_score(post: Post, agent: Agent) -> float:
    base_score = embedding_similarity(post, agent.interests)
    
    # Engagement signals
    velocity_boost = post.velocity * VELOCITY_WEIGHT
    
    # Media boost (per X's documented heuristics)
    media_boost = MEDIA_MULTIPLIER if post.has_media else 1.0  # e.g., 2x-10x
    
    return base_score * velocity_boost * media_boost
```

This ensures visual posts surface more prominently in preference-based feeds, matching real platform behavior.

**What This Design Tests:**

1. **Direct effect**: Do agents engage more with posts marked as having images?
2. **Algorithmic amplification**: Does the media boost in ranking create feedback loops?
3. **Cascade patterns**: Do visual posts generate deeper/wider reshare trees?
4. **Interaction effects**: Is the visual advantage stronger under algorithmic curation vs random feeds?

### Phased Testing Plan

#### Phase 1: MVP (A/B or Multi-Arm)
- **Goal**: Detect if visuals have meaningful effect; validate simulation basics.
- **Design**: 4 scenarios (2×2: visuals × feed mode).
- **Replications**: 20-50 per scenario with random seeds.
- **Execution**: CLI batch mode via Agent Framework workflow.
- **Analysis**:
  - Descriptive: Medians/SD/distributions (pandas, matplotlib boxplots).
  - Statistical: Mann-Whitney U, effect sizes (Cohen's d).
  - Qualitative: Cascade visualizations (NetworkX).
- **Decision Gate**: Strong signal (≥1.5x effect, p<0.05) → Phase 2.

#### Phase 2: Multifactorial DOE (If Justified)
- **Goal**: Quantify interactions (visuals × controversy × velocity).
- **Design**: Fractional factorial or Latin Hypercube Sampling via pyDOE/SALib.
- **Replications**: 10-20 per design point.
- **Analysis**: Main effects/interaction plots, ANOVA, Sobol sensitivity indices.

## User Stories

1. **As a researcher**, I want to load a Twitter dataset so I can bootstrap agents with real profiles.
2. **As a developer**, I want to configure recommendation modes (X-algo, preference, random) to test virality impacts.
3. **As an experimenter**, I want to run simulations with seeded content to measure cascade growth.
4. **As an analyst**, I want visualized metrics and OpenTelemetry traces to understand simulation dynamics.
5. **As a user**, I want to swap between Ollama and cloud LLMs without changing my experiment code.
6. **As a user testing hypotheses**, I want built-in support for phased studies (A/B MVP to DOE).

## Technical Architecture

### High-Level Diagram
```
┌─────────────────────────────────────────────────────────────────────┐
│                         PRISM Architecture                          │
│     Platform Replication for Information Spread Modeling            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐    ┌─────────────────────────────────────────┐    │
│  │ Twitter Data │───▶│         Data Pipeline                   │    │
│  │   (CSV/JSON) │    │  • Bot filtering                        │    │
│  └──────────────┘    │  • Trait inference (KeyBERT/BERT)       │    │
│                      │  • Profile generation                    │    │
│                      └─────────────────┬───────────────────────┘    │
│                                        │                             │
│                                        ▼                             │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │              Microsoft Agent Framework (Python)              │    │
│  │  ┌─────────────────────────────────────────────────────┐    │    │
│  │  │                 Workflow Orchestration               │    │    │
│  │  │   ┌──────────┐   ┌──────────┐   ┌──────────┐       │    │    │
│  │  │   │  Feed    │──▶│  Agent   │──▶│  State   │       │    │    │
│  │  │   │ Retrieval│   │ Decision │   │  Update  │       │    │    │
│  │  │   └──────────┘   └──────────┘   └──────────┘       │    │    │
│  │  │        │              │              │              │    │    │
│  │  │        ▼              ▼              ▼              │    │    │
│  │  │   ┌─────────────────────────────────────────┐      │    │    │
│  │  │   │         OpenTelemetry Tracing           │      │    │    │
│  │  │   └─────────────────────────────────────────┘      │    │    │
│  │  └─────────────────────────────────────────────────────┘    │    │
│  │                           │                                  │    │
│  │  ┌────────────────────────┼────────────────────────┐        │    │
│  │  │                        ▼                        │        │    │
│  │  │  ┌──────────────┐  ┌──────────────┐            │        │    │
│  │  │  │ ChatAgent    │  │ ChatAgent    │  ... ×1000 │        │    │
│  │  │  │ (Profile A)  │  │ (Profile B)  │            │        │    │
│  │  │  └──────┬───────┘  └──────┬───────┘            │        │    │
│  │  │         │                 │                     │        │    │
│  │  │         └────────┬────────┘                     │        │    │
│  │  │                  ▼                              │        │    │
│  │  │         IChatClient Abstraction                 │        │    │
│  │  └──────────────────┬──────────────────────────────┘        │    │
│  └─────────────────────┼───────────────────────────────────────┘    │
│                        │                                             │
│           ┌────────────┼────────────┐                               │
│           ▼            ▼            ▼                               │
│  ┌──────────────┐ ┌─────────┐ ┌───────────┐                        │
│  │    Ollama    │ │ Azure   │ │  OpenAI   │  (LLM Providers)       │
│  │ (localhost)  │ │ OpenAI  │ │   API     │                        │
│  │  Mistral 7B  │ │         │ │           │                        │
│  └──────────────┘ └─────────┘ └───────────┘                        │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    Supporting Services                       │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │    │
│  │  │   ChromaDB   │  │  X Algo      │  │  NetworkX    │       │    │
│  │  │  (RAG/Feed)  │  │  (Ranking)   │  │  (Cascades)  │       │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘       │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    Analytics & Export                        │    │
│  │  • Metrics (Pandas) • Visualizations (Matplotlib/NetworkX)  │    │
│  │  • DOE Integration (pyDOE/SALib) • JSON/CSV Export          │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology | Notes |
|-----------|------------|-------|
| **Orchestration** | Microsoft Agent Framework (Python) | `pip install agent-framework --pre` |
| **LLM (Primary)** | Ollama + gpt-oss:20b | 21B params, 3.6B active MoE, ~3.1s/inference |
| **LLM (Development)** | Ollama + Mistral 7B | Fast iteration, ~0.8s/inference |
| **LLM (Fallback)** | Azure OpenAI, OpenAI | Via IChatClient abstraction |
| **Vector Store** | ChromaDB | RAG for feed retrieval |
| **Embeddings** | sentence-transformers / Ollama | Local embedding models |
| **Graph Analysis** | NetworkX | Cascade tracking, homophily |
| **Data Processing** | Pandas | Metrics, analysis |
| **Visualization** | Matplotlib, NetworkX | Graphs, plots |
| **Observability** | OpenTelemetry | Built into Agent Framework |
| **DOE** | pyDOE, SALib | Experiment design |
| **Trait Inference** | KeyBERT, YAKE, transformers | Profile generation |

### Hardware Target
- **Primary**: M3 Ultra Mac Studio, 512GB unified memory
- **Ollama Config**: 2-4 parallel model instances for throughput
- **Memory Budget**: ~200GB for simulation state, ~100GB for Ollama models, headroom for OS/tools

### Performance Estimates (Benchmarked on M3 Ultra)

**Single inference benchmarks:**
| Model | Total Time | Output Tokens | Generation Rate |
|-------|------------|---------------|-----------------|
| gpt-oss:20b | ~3.1s | ~292 (with CoT) | 103 tok/s |
| Mistral 7B | ~0.8s | ~75 | 105 tok/s |

**Simulation run estimates (gpt-oss:20b primary):**
| Agents | Rounds | Inferences | Serial Time | 2x Parallel | 4x Parallel |
|--------|--------|------------|-------------|-------------|-------------|
| 100 | 50 | 5,000 | ~4.2 hrs | ~2.1 hrs | ~1 hr |
| 250 | 50 | 12,500 | ~10.4 hrs | ~5.2 hrs | ~2.6 hrs |
| 500 | 50 | 25,000 | ~20.8 hrs | ~10.4 hrs | ~5.2 hrs |

**Recommended configurations:**
- **Development/iteration**: 100 agents, Mistral 7B (~1 hr runs)
- **Validation runs**: 250 agents, gpt-oss:20b (~2.6 hrs with 4x parallel)
- **Full experiments**: 500 agents, gpt-oss:20b (overnight runs, ~5 hrs with 4x parallel)
- **Replications**: 20-50 per experiment condition

## Success Metrics

| Category | Metric | Target |
|----------|--------|--------|
| **Functional** | Fidelity to paper results | 90% replication of preference-mode boost |
| **Quality** | Agent decision realism | Human evaluators rate outputs as "realistic" >70% |
| **Usability** | Commands to run full sim | <5 CLI commands |
| **Performance** | Single run completion (250 agents) | <3 hours with 4x parallelization |
| **Observability** | Trace coverage | 100% of agent decisions traced |
| **Study Outcomes** | Hypothesis validation | Complete phased study (visuals hypothesis) |
| **Adoption** | Open-source release | GitHub repo with docs and examples |

## Timeline and Milestones

| Week | Milestone | Deliverables |
|------|-----------|--------------|
| 1-2 | **Foundation** | Agent Framework + Ollama integration, basic ChatAgent working |
| 3 | **RAG System** | ChromaDB integration, feed retrieval modes |
| 4 | **Simulation Loop** | Workflow orchestration, state management, round execution |
| 5 | **X Algorithm** | Ranking heuristics port, candidate sourcing |
| 6 | **Data Pipeline** | Twitter data ingestion, trait inference, profile generation |
| 7 | **Observability** | OpenTelemetry setup, metrics collection, visualization |
| 8 | **Experimentation** | A/B framework, CLI batch mode, MVP hypothesis test |
| 9 | **DOE Integration** | pyDOE/SALib, Phase 2 experiment support |
| 10 | **Polish & Docs** | Documentation, examples, open-source release prep |

## Appendices

### A. References
- Ferraro et al. Paper: arXiv 2411.16031
- X Algo Repo: github.com/xai-org/x-algorithm (reference for heuristics)
- Microsoft Agent Framework: github.com/microsoft/agent-framework
- Agent Framework Docs: learn.microsoft.com/en-us/agent-framework
- Similar Tools: MOSAIC/OASIS, tsinghua-fib-lab/LLM-Agent-Based-Modeling

### B. Agent Framework Resources
- Getting Started: https://learn.microsoft.com/en-us/agent-framework/tutorials/quick-start
- Ollama Integration: https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-types/chat-client-agent
- Workflow Samples: github.com/microsoft/agent-framework/tree/main/python/samples/getting_started/workflows
- Awesome Agent Framework: github.com/webmaxru/awesome-microsoft-agent-framework

### C. Ollama Setup
```bash
# Install Ollama (macOS)
brew install ollama

# Pull primary model
ollama pull gpt-oss:20b

# Pull development/fallback models
ollama pull mistral
ollama pull nomic-embed-text  # For embeddings

# Run Ollama server
ollama serve

# Verify
curl http://localhost:11434/api/tags

# Test gpt-oss:20b with verbose stats
ollama run gpt-oss:20b --verbose "Test prompt here"
```

**gpt-oss:20b configuration notes:**
- Reasoning effort can be set via system prompt: `Reasoning: low`, `Reasoning: medium`, or `Reasoning: high`
- Use `Reasoning: low` for faster responses without chain-of-thought
- Native tool calling supported for structured agent decisions
- 128K context window supports long conversation histories

### D. Project Structure (Proposed)
```
prism/
├── pyproject.toml
├── README.md
├── prism/
│   ├── __init__.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── social_agent.py      # ChatAgent wrapper
│   │   ├── profiles.py          # Profile generation
│   │   └── prompts.py           # Prompt templates
│   ├── workflows/
│   │   ├── __init__.py
│   │   ├── simulation.py        # Main simulation workflow
│   │   └── executors.py         # Feed, decision, state executors
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── feed_retriever.py    # ChromaDB integration
│   │   └── embeddings.py        # Embedding utilities
│   ├── ranking/
│   │   ├── __init__.py
│   │   └── x_algorithm.py       # X ranking heuristics
│   ├── data/
│   │   ├── __init__.py
│   │   ├── ingestion.py         # Data loading
│   │   └── preprocessing.py     # Trait inference
│   ├── metrics/
│   │   ├── __init__.py
│   │   ├── cascades.py          # NetworkX analysis
│   │   └── virality.py          # Virality metrics
│   ├── experiments/
│   │   ├── __init__.py
│   │   ├── runner.py            # Experiment orchestration
│   │   └── doe.py               # pyDOE/SALib integration
│   └── cli/
│       ├── __init__.py
│       └── main.py              # CLI entry point
├── configs/
│   ├── default.yaml
│   └── experiments/
│       └── visuals_hypothesis.yaml
├── data/
│   └── .gitkeep
├── outputs/
│   └── .gitkeep
└── tests/
    └── ...
```

### E. Next Steps
1. Create GitHub repo: `prism` (Platform Replication for Information Spread Modeling)
2. Set up project skeleton with proposed structure
3. Install Agent Framework preview: `pip install agent-framework --pre`
4. Prototype single-agent decision loop with Ollama + gpt-oss:20b
5. Validate throughput on M3 Ultra with 100-agent batch
6. Integrate ChromaDB for RAG feed retrieval
7. Iterate toward full workflow orchestration