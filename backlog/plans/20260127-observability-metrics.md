---
title: "Observability and Metrics"
status: open
priority: medium
created: 2026-01-27
depends_on: ["20260127-simulation-workflow-loop.md"]
---

# Observability and Metrics

## Summary

Integrate OpenTelemetry for tracing agent decisions and state transitions, implement virality metrics (cascade size, depth, resharing rates), and add visualization capabilities for experiment analysis.

## Motivation

The PRD targets 100% trace coverage for agent decisions. Researchers need to understand why cascades form, debug unexpected behavior, and validate simulation realism. Metrics like homophily and cascade depth are core outputs for hypothesis testing.

## Proposal

### Goals

- Configure OpenTelemetry tracing via Agent Framework's built-in integration
- Export traces to Jaeger/Zipkin for development visualization
- Implement virality metrics: cascade size, depth, resharing rates, time-to-virality
- Add network analysis metrics: homophily (assortativity) via NetworkX
- Create visualization utilities for cascade graphs and metric plots

### Non-Goals

- Production monitoring infrastructure
- Real-time dashboards
- Custom tracing backends

## Design

Per PRD §4.7, observability wraps around the simulation workflow:

1. **OpenTelemetry Setup**
   - Enable Agent Framework's built-in tracing
   - Configure exporter for Jaeger (development) or JSON (batch analysis)
   - Span per agent decision, tool call, and state transition
2. **Metrics Collection**
   - Per-round: engagement rates, active agents, new posts
   - Per-cascade: size, depth, velocity, reshare tree structure
   - Per-simulation: homophily coefficient, virality threshold detection
3. **Cascade Tracking**: NetworkX graph of reshare relationships
4. **Visualization**: Matplotlib for metric plots, NetworkX for cascade graphs
5. **Export**: JSON/CSV for external analysis tools (pyDOE/SALib integration)

## Tasks

- [ ] Configure OpenTelemetry with Jaeger exporter
- [ ] Add tracing spans to workflow executors (feed, decision, state, logging)
- [ ] Implement cascade tracking with NetworkX directed graph
- [ ] Calculate virality metrics (size, depth, velocity, time-to-N-reshares)
- [ ] Calculate network metrics (homophily/assortativity coefficient)
- [ ] Add visualization utilities (cascade graphs, engagement plots)
- [ ] Implement JSON/CSV export for metrics and traces
