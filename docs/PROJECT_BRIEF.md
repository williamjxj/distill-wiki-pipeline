---
type: project-brief
status: current
date: '2026-05-26'
export_cycle: 2
sources_ingested: 6
---

# Project Brief: Multi-LLM Research Pipeline

## Problem

The problem addresses **context fragmentation** in AI-assisted engineering, where developers face scattered, duplicated, and contradictory information from various sources like chatbots (ChatGPT, Claude, Gemini), documentation, GitHub, and other knowledge repositories. This context fragmentation leads to incomplete architecture and conflicting instructions, causing coding agents to fail.

## Current Understanding

The project aims to implement Karpathy's **LLM-Wiki pattern** as a multi-LLM research → distillation → dev-tool handoff pipeline. The key insights include:
1. **Context Fragmentation**: Engineers accumulate scattered information from various sources.
2. **Contradictions Tracking**: Multi-LLM outputs often amplify hallucinations, making it necessary to track and resolve contradictions.
3. **Compounding Knowledge Layer**: The LLM-Wiki is a persistent, compounding artifact that addresses the RAG (Relevant Answer Generation) ephemerality problem.
4. **Human Review Gate**: Mandatory checkpoint between wiki distillation and dev context packaging ensures correctness before deployment.

## Chosen Approach

The chosen approach involves:
1. **Multi-LLM Collection** with identical prompts → immutable `raw/llm/`.
2. **Wiki Distillation** via multi-pass distillation, semantic deduplication, contradictions tracking.
3. **Compounding Knowledge Layer**: Persistent markdown graph with decision records, cross-references, supersession mechanisms; steered by purpose steering.
4. **Human Review Gate**: Ensures correctness before dev context export.
5. **Dev Tools Handoff** via export-brief for Cursor and Claude Code.
6. **Closed-Loop Harvesting**: Dev session logs back to `raw/sessions/` for re-ingestion.

### Constraints

- Ingest one source at a time, lint every 3–5 ingests.
- MVP remains markdown wiki submodule pattern (markdown + git + Obsidian viewer).
- Add automation incrementally: OpenKB, embedding dedup, session harvesters are post-MVP.
- Use purpose-built operators with human approval gates for MCP.

### Non-Goals

- Full-fledged UI for dev tools and MCP.
- Embedding-based deduplication at MVP level; scale post-MVP.

## Rejected Alternatives

| Alternative | Reason |
|-------------|--------|
| Continuous Feedback + Memory (Claude) vs. Automated Harvester Adapters (Gemini) | Gemini's automated adapters are more practical for initial implementation. |
| Embedding-based Deduplication at MVP Level | Post-MVP due to resource constraints and focus on core functionality. |
| Open WebUI Pipelines for Operator UI | Ollama-backed workflows with human approval gates are preferred.

## Open Questions

- When to add embedding-based dedup (ChatGPT) vs staying LLM-only for MVP?
- Which external tool to evaluate first: OpenKB, Nashsu, Pratiyush, obsidian-llm-wiki, qmd?
- How to implement closed-loop harvesting for Cursor session logs?
- Should `purpose.md` live in the parent project root or wiki submodule?
- Phase 3 compile automation — prompt template vs script vs export-brief skill?
- Karpathy's original gist not yet ingested as primary source — worth adding?