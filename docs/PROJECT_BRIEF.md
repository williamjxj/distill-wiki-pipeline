---
type: project-brief
status: current
date: 2026-05-29
export_cycle: 4
sources_ingested: 9
---

# Project Brief: LLM-Wiki Handoff Pipeline

## Problem

**Context fragmentation** — engineers collect scattered, duplicated, contradictory outputs from multiple LLMs (ChatGPT, Claude, Gemini), web articles, docs, PDFs, and notes with no canonical source of truth. Coding agents fail because they receive bad context: incomplete architecture, conflicting instructions, and noisy raw chat dumps. The core problem is not model capability — it's context engineering.

## Current Understanding

The project builds Karpathy's **LLM-Wiki pattern** as a multi-LLM research → distillation → dev-tool handoff pipeline. 9 sources across 3 LLMs and 2 web articles converge on a unified architecture:

- **Epistemic foundation**: LLM outputs are first-pass synthetic knowledge, not ground truth ([[llm-outputs-as-synthetic-sources]]). Signal emerges only through distillation.
- **Pipeline**: Multi-LLM Collection → [[two-stage-ingestion]] (analysis → generation) → [[multi-pass-distillation]] with [[semantic-deduplication]] → [[decision-records]] with source attribution → [[context-packs]] → dev tools.
- **Knowledge layer**: A [[compounding-knowledge-layer]] (persistent markdown graph) replaces ephemeral RAG. [[contradictions-tracking]] with UNRESOLVED/SUPERSEDED flags, [[decision-records]] with provenance, and decay-weighted confidence scoring.
- **Disciplines**: [[human-review-gate]] with concrete quality criteria (zero filler, versioned tools, explicit tradeoffs, ≥3 gotchas). Ingest one at a time. Lint every 3–5 ingests. Never feed unreviewed synthesis to code agents.
- **North star**: [[implementation-readiness]] — "Can Cursor implement this correctly?"

## Chosen Approach

**Pipeline architecture** ([[pipeline-operator]]): Python core module with three interfaces — CLI (argparse/typer), Open WebUI Pipelines plugin, MCP server (fastmcp). All call into shared `pipeline/runner.py`. Build order: core → CLI → MCP → Web UI.

**Ingestion** ([[two-stage-ingestion]]): Stage 1 (read-only structural analysis → blueprint), Stage 2 (execute blueprint, write pages, update links). [[purpose-steering]] via dedicated `purpose.md` file read before every ingest.

**Distillation** ([[multi-pass-distillation]]): Collect (20 min, same 3–5 seed questions across LLMs) → Filter (10 min, 5-signal test: Specificity, Actionability, Non-obviousness, Consensus, Contradiction) → Distill (30 min, synthesize, frame conflicts as tradeoffs) → Canonical (15 min, dense markdown with frontmatter, facts, code, tradeoffs, gotchas). ~80 min per topic.

**Compression** ([[context-compression]]): Two-level — research pipeline (10K pages → 20 pages → 2 pages) and API call level (sliding window, summarization, hard truncation).

**Context delivery** ([[context-packs]]): Per-module bundles (architecture, APIs, schema, constraints, conventions, implementation order) + standardized exports (llms.txt, llms-full.txt, graph.jsonld) + portable SKILL.md packages + tool-specific integration files (CLAUDE.md, .cursorrules, AGENTS.md).

**Closed loop** ([[closed-loop-harvesting]]): Dev session logs harvested back into `raw/sessions/` for re-ingestion, flagging discrepancies between generated code and planned architecture.

## Constraints

- All content is markdown + git (human-readable, version-controlled, no vendor lock-in)
- CLI-first: UI comes post-MVP ([[mvp-scope]])
- Local-first: MCP server runs locally, no external hosting needed
- Tool-agnostic: works with Cursor, Claude Code, OpenCode, VS Code Copilot
- Pipeline quality over features: dirty-only reprocessing to avoid token waste

## Non-Goals

- Full vector database or graph database in MVP (threshold: ~hundreds of pages)
- Automated collection from LLM APIs (manual paste for now)
- Real-time collaboration or multi-user features
- Obsidian plugin development (Obsidian as viewer, not a dependency)
- Commercial product packaging (infrastructure for now)

## Rejected Alternatives

| Alternative | Why Rejected |
|-------------|-------------|
| AnythingLLM for Web UI | Open WebUI Pipelines maps better to ETL stages; AnythingLLM is for RAG/Q&A |
| Pure RAG pipeline | Ephemeral — doesn't compound knowledge across sessions |
| Ollama-only stack | Too slow for production use; cloud LLMs for reasoning, Ollama for background tasks |
| "Wiki" as product name | Kept as architectural name; "Context Engine" acknowledged for future product positioning |

## Open Questions

1. Should seed questions be stored as templates for repeatable multi-LLM collection?
2. What is the right threshold for automatic supersession vs human-resolved contradiction?
3. How should confidence scores be calibrated across different LLM sources?
4. What's the optimal chunk size for embedding-based dedup in this domain?
