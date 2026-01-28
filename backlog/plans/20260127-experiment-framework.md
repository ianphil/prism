---
title: "Experiment Framework and CLI"
status: open
priority: medium
created: 2026-01-27
depends_on: ["20260127-simulation-workflow-loop.md", "20260127-x-algorithm-ranking.md", "20260127-observability-metrics.md"]
---

# Experiment Framework and CLI

## Summary

Build the experimentation infrastructure including CLI for running simulations, A/B testing framework, batch execution with replications, and DOE integration for multifactorial studies.

## Motivation

PRISM's value is in enabling controlled experiments on virality. The PRD outlines a phased testing approach (A/B MVP → DOE) and requires <5 CLI commands to run a full simulation. This framework makes hypothesis testing accessible to researchers.

## Proposal

### Goals

- Create CLI entry point for running experiments and visualizing results
- Implement A/B/multi-arm experiment runner with configurable scenarios
- Support batch execution with replications (20-50 per condition)
- Integrate pyDOE/SALib for factorial designs and sensitivity analysis
- Enable YAML-driven experiment configuration

### Non-Goals

- Web UI for experiment management
- Distributed execution across multiple machines
- Automated hypothesis generation

## Design

Per PRD §5, the framework supports phased experimentation:

1. **CLI Interface** (`prism` command)
   - `prism run <config.yaml>` - Execute single simulation
   - `prism experiment <experiment.yaml>` - Run batch with replications
   - `prism analyze <output_dir>` - Generate metrics and visualizations
2. **Experiment Runner**
   - Load experiment config (scenarios, variables, replications)
   - Execute simulations with random seeds for reproducibility
   - Aggregate results across replications
3. **A/B Framework**: Compare conditions (e.g., visuals × feed mode → 2×2 design)
4. **DOE Integration**: pyDOE for factorial designs, SALib for Sobol sensitivity
5. **Analysis Pipeline**: Descriptive stats, Mann-Whitney U, effect sizes, ANOVA

## Tasks

- [ ] Create CLI entry point with Click/Typer (`prism/cli/main.py`)
- [ ] Implement `prism run` command for single simulation execution
- [ ] Define experiment YAML schema (scenarios, variables, replications, seeds)
- [ ] Implement experiment runner with batch execution and seed management
- [ ] Add `prism experiment` command for multi-scenario runs
- [ ] Integrate pyDOE for factorial/Latin Hypercube designs
- [ ] Implement `prism analyze` with stats (Mann-Whitney, Cohen's d) and plots
