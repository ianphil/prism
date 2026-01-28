---
title: "Data Pipeline: Ingestion and Profile Generation"
status: open
priority: medium
created: 2026-01-27
depends_on: ["20260127-foundation-agent-framework-ollama.md"]
---

# Data Pipeline: Ingestion and Profile Generation

## Summary

Build the data pipeline for loading real Twitter datasets, inferring user traits, filtering bots, and generating agent profiles that bootstrap realistic simulation behavior.

## Motivation

Agent realism depends on grounding in real social media patterns. The PRD emphasizes reproducibility and validation against real data. This pipeline transforms raw Twitter exports into agent profiles with inferred interests, personality traits, and political stance.

## Proposal

### Goals

- Load Twitter datasets from CSV/JSON formats
- Filter bot accounts using available signals (Botometer scores if present)
- Infer agent traits: interests via KeyBERT/YAKE, stance via BERT classifier
- Generate agent profiles from user metadata
- Support synthetic agent generation as fallback option

### Non-Goals

- Real-time web scraping (use pre-loaded datasets only)
- Fine-tuning ML models on custom data
- Handling streaming data ingestion

## Design

Per PRD §4.6, the pipeline has three stages:

1. **Ingestion**: Load tweets and user metadata from CSV/JSON files
   - Schema validation for required fields
   - Configurable column mapping for different dataset formats
2. **Preprocessing**
   - Bot filtering: Exclude accounts with high Botometer scores or bot-like patterns
   - Trait inference: KeyBERT/YAKE for interest extraction, transformer classifier for stance
   - Profile aggregation: Combine tweets per user into trait vectors
3. **Profile Generation**
   - Create `AgentProfile` with name, interests, personality, stance
   - Generate system prompts from profile data
   - Support synthetic profile generation for controlled experiments

## Tasks

- [ ] Define `AgentProfile` dataclass (interests, personality, stance, metadata)
- [ ] Implement dataset loader with CSV/JSON support and schema validation
- [ ] Add bot filtering logic (Botometer threshold, pattern detection)
- [ ] Integrate KeyBERT/YAKE for interest extraction from tweet history
- [ ] Add stance classifier using pre-trained transformer
- [ ] Implement profile-to-prompt generator for agent initialization
- [ ] Write tests: loading, filtering, trait extraction accuracy
