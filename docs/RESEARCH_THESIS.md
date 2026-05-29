---
type: synthesis
status: evolving
last_updated: 2026-05-29
sources_ingested: 9
---

# Evolving Thesis

> Running synthesis across all ingested sources. Updated after every ingest.

## Current Understanding

This project implements Karpathy's **LLM-Wiki pattern** as a multi-LLM research → distillation → dev-tool handoff pipeline. The first source (ChatGPT) validates the core direction and provides foundational concepts.

**Problem:** [[context-fragmentation]] — scattered, duplicated, contradictory research across LLMs and sources. Coding agents fail from bad context, not bad models.

**Epistemic reframe** ([[llm-outputs-as-synthetic-sources]]): LLM chat exports are first-pass synthetic knowledge, not ground truth. The wiki distillation layer is where signal emerges.

**Pipeline** ([[multi-pass-distillation]]): raw → clustered → summarized → canonicalized → implementation-oriented, progressing through [[semantic-deduplication]] and [[decision-records]].

**Knowledge layer** ([[compounding-knowledge-layer]]): persistent markdown graph with decisions, cross-refs, supersession — not ephemeral RAG.

**North star:** [[implementation-readiness]] — "Can Cursor implement this correctly?" determines quality.

**Outputs:** [[context-packs]] — per-module bundles for agentic tools.

**Moat:** [[context-compression]] — multi-tier compression from raw research to implementation prompts.

**Contradictions** ([[contradictions-tracking]]): explicit UNRESOLVED flags for multi-LLM disagreements — "where multi-LLM input earns its keep."

**Human review** ([[human-review-gate]]): non-negotiable gate between wiki distillation and dev tool handoff.

**Operational rhythm:** ingest one at a time; lint every 3–5 ingests; human review before export.

**Pipeline phases** ([[research-to-implementation-pipeline]]): Multi-LLM Collection → Wiki Distillation → Dev Context Package → Dev Tools.

**Cross-source synthesis** ([[wiki-vs-context-engine]]): the pattern is called "LLM-Wiki" (Karpathy's original) while acknowledging the product distinction.

**Decision provenance** ([[decision-records]]): each decision captures source attribution and runner-up alongside rationale and confidence.

**Closed feedback loop** ([[closed-loop-harvesting]]): insights discovered during dev get harvested back into raw/ for re-ingest.

**Intent guidance** ([[purpose-steering]]): project-level schema/constraints steer wiki behavior.

**Ingestion method** ([[two-stage-ingestion]]): structural analysis before page generation, one source at a time.

**Pipeline operator** ([[pipeline-operator]]): Python core module with three interfaces — CLI, Open WebUI Pipelines plugin, MCP server.

**Build order:** core → CLI scripts → MCP server → Open WebUI plugin.

**MVP** ([[mvp-scope]]): CLI-first, markdown + git, no UI. Pipeline quality over features.

### Thesis Delta: ChatGPT — Foundational Concepts

Source 1 ([[chatgpt-llm-based-project-workflow]]) establishes the core problem framing and provides 10 foundational concepts:

- **Context fragmentation** identified as the real engineering problem — not coding ability
- **Semantic deduplication** called out as the most critical pipeline stage
- **Decision-first storage** (decision + rationale + confidence + tradeoffs) preferred over unstructured notes
- **Context compression** framed as the competitive moat vs better models
- **Implementation readiness** as the north star success criterion

### Thesis Delta: Claude — Operational Structure

Source 2 ([[claude-multi-llm-research-synthesis-workflow]]) adds the operational layer that ChatGPT's vision lacked:

- **4-phase pipeline** defined explicitly: Collection → Wiki Distillation → Dev Context Package → Dev Tools
- **Contradictions tracking** as a dedicated wiki component with UNRESOLVED flags
- **Human review gate** as non-negotiable between distillation and dev handoff
- **Lint rhythm** of every 3–5 ingests to catch contradictions, orphans, stale claims
- **Decision records** expanded with source attribution and confidence levels
- **Closed-loop harvesting** — query answers and dev session insights feed back into the wiki

### Thesis Delta: Gemini — Implementation Specification

Source 3 ([[gemini-llm-wiki-multi-agent]]) provides the most detailed implementation specifications:

- **Two-stage ingestion formalized**: Stage 1 (read-only structural analysis → blueprint) → Stage 2 (execute blueprint, write pages)
- **purpose.md intent steering**: dual-file schema (schema.md + purpose.md) prevents knowledge drift
- **Decay-weighted confidence scoring**: claims carry Ebbinghaus-style exponential decay
- **Systematic supersession**: contradictions resolved through stale-archival with timestamped links
- **Graph-layered entity extraction**: typed entities (Project, Library, API) with typed relations (depends_on, supersedes)
- **Hierarchical tree indexing** (PageIndex): for documents >20 pages, skip flat chunking
- **Machine-readable exports**: llms.txt, llms-full.txt (≤5MB), graph.jsonld
- **Portable agent skills**: wiki subdirectories → SKILL.md packages → ~/.claude/skills/
- **Obsidian MCP integration**: real-time IDE↔wiki connection via MCP tools

### Thesis Delta: Claude — Pipeline Implementation Plan

Source 4 ([[2026-05-25-cluade-pipeline-plan]]) transitions from research to operational implementation:

- **Pipeline operator** ([[pipeline-operator]]): Python core with config.yaml, ingest/refine/synthesize/export stages, SQLite run-state tracking
- **Build order established**: core → CLI scripts → MCP server → Open WebUI plugin
- **MCP server with fastmcp**: 5 tools (run_pipeline, get_article, list_articles, get_run_status, search_wiki)
- **Open WebUI Pipelines** as the Web UI layer — `/run`, `/status`, `/preview` as chat commands
- **Dirty-only reprocessing**: SQLite tracks changes to avoid token waste on unchanged content

### Thesis Delta: Distill-Ingest — Methodology Guide

Source 5 ([[distill-ingest]]) provides the rigorous methodology that earlier sources advocated for in principle:

- **5-signal filter** formalizes [[multi-pass-distillation]]: score on Specificity, Actionability, Non-obviousness, Consensus, Contradiction — keep only 3+
- **Conflict → Decision Space** reframes [[contradictions-tracking]]: LLM disagreements define the design space, not bugs
- **Distillation quality gate** adds concrete criteria to [[human-review-gate]]: zero filler, versioned tools, explicit tradeoffs, ≥3 gotchas
- **Tool-specific ingest files** extends [[context-packs]]: CLAUDE.md, .cursorrules, AGENTS.md, copilot-instructions.md per tool
- **Tiered automation**: no-code (Obsidian) → agent-assisted → MCP → ETL pipeline — don't overbuild

### Thesis Delta: Distill-Canonical — Summary & Decision Heuristic

Source 6 ([[2026-05-26-claude-distill-canonical]]) is a short summary — two key additions:

- **When to multi-source heuristic**: only for complex/architectural/long-lived topics. Different LLMs have genuinely different knowledge distributions.
- **MemWeaver MCP path**: existing `/query`/`/ingest`/`/chat` endpoints map directly to MCP tools

### Thesis Delta: Claude-04-Summary — Autoresearch & Reference Material

Source 7 ([[2026-05-27-claude-04-summary]]) is a personal notes document adding:

- **Karpathy autoresearch pattern** as a complementary loop to llm-wiki: automate the research phase, then structure via wiki
- **5 AI workflows** template for task decomposition in agentic coding
- **Chinese LLM API reference** (DeepSeek, Kimi, MiniMax, GLM) for practical tool integration

### Thesis Delta: Doubao — Token & Memory Management

Source 8 ([[doubao]]) adds practical API-level context management:

- **API token strategies**: sliding window, hard truncation, dialogue summarization, key info extraction — operationalizing [[context-compression]] at the API call level
- **Memory architecture**: short-term + long-term + RAG + consolidation/forgetting — practical knowledge lifecycle management

### Thesis Delta: S2-NotebookLM — Local Memory Manager & Scaling

Source 9 ([[s2-notebooklm]]) adds:

- **Local Memory Manager**: Ollama for background compilation, keeping cloud costs low
- **Scaling threshold**: vector/graph indexing needed when wiki exceeds ~hundreds of pages
- **Agent Skills Layer**: SKILL.md per domain — aligns with Gemini's portable agent skills ([[context-packs]])

## Thesis Deltas
