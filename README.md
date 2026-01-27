# PRISM

**Platform Replication for Information Spread Modeling**

A generative agent-based social media simulator for studying virality and information spread.

## Overview

PRISM is a Python-based toolkit for running generative agent-based simulations of Twitter/X-like platforms. It combines LLM-driven agents with RAG-based feed simulation and X's open-sourced recommendation algorithm to enable controlled experiments on content virality.

## Key Features

- **Quality-first**: gpt-oss:20b provides human-like agent reasoning for realistic social simulation
- **Local-first**: Full simulation runs on consumer hardware via Ollama, no cloud API costs
- **Modular**: Swap LLM providers (Ollama, Azure, OpenAI) via IChatClient abstraction
- **Observable**: Built-in OpenTelemetry integration for tracing and debugging
- **Reproducible**: Config-driven simulations with checkpointing and logging

## Target Users

- Researchers in social sciences, AI, or computational sociology
- Developers building agentic AI tools
- Platform designers testing algorithm impacts

## Hardware Target

- Primary: M3 Ultra Mac Studio, 512GB unified memory
- Supports 250-500 agent simulations with Ollama parallelization

## Tech Stack

| Component | Technology |
|-----------|------------|
| Orchestration | Microsoft Agent Framework (Python) |
| LLM (Primary) | Ollama + gpt-oss:20b |
| LLM (Dev) | Ollama + Mistral 7B |
| Vector Store | ChromaDB |
| Graph Analysis | NetworkX |
| Observability | OpenTelemetry |

## Status

Early development. See `aidocs/prd.md` for full requirements.
