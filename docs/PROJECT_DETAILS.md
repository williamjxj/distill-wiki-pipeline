---
type: project-details
status: current
date: 2026-05-29
export_cycle: 4
sources_ingested: 9
paired_brief: project-brief
---

# Project Details: LLM-Wiki Handoff Pipeline

## Source Map

| # | Slug | Source | Type | Length | Primary Contribution |
|---|------|--------|------|--------|---------------------|
| 1 | [[chatgpt-llm-based-project-workflow]] | ChatGPT | LLM chat | 615 lines | Core concepts, problem framing, context compression as moat |
| 2 | [[claude-multi-llm-research-synthesis-workflow]] | Claude | LLM chat | 143 lines | 4-phase pipeline, contradictions tracking, human review gate |
| 3 | [[gemini-llm-wiki-multi-agent]] | Gemini | LLM chat | 262 lines | Two-stage ingestion, purpose.md, decay-weighted confidence, graph-typed entities |
| 4 | [[2026-05-25-cluade-pipeline-plan]] | Claude | LLM chat | 150 lines | Pipeline implementation plan: Python core, Open WebUI, MCP, CLI |
| 5 | [[distill-ingest]] | Claude | LLM chat | 598 lines | Methodology: 5-signal filter, quality gate, tool-specific ingest, tiered automation |
| 6 | [[2026-05-26-claude-distill-canonical]] | Claude | LLM chat | 30 lines | Multi-source decision heuristic, MemWeaver MCP path |
| 7 | [[2026-05-27-claude-04-summary]] | Claude | LLM chat | 185 lines | Autoresearch pattern, Chinese LLM API reference, tool landscape |
| 8 | [[doubao]] | Web | Web article | 57 lines | API-level token/memory management, sliding window, memory architecture |
| 9 | [[s2-notebooklm]] | Web | Web article | 61 lines | Local Memory Manager (Ollama), scaling threshold, Agent Skills Layer |

## Combined Understanding

### The Core Problem: Context Fragmentation

Every source independently identifies the same root problem: engineers accumulate scattered, duplicated, contradictory outputs from multiple LLMs and sources. The result is that agentic coding tools (Cursor, Claude Code, OpenCode) receive polluted context — conflicting instructions, incomplete architecture, noisy raw chat dumps. Coding agents fail not because models are weak, but because **context engineering is broken**.

ChatGPT states it most directly: "The biggest problem today is NOT coding. It is context fragmentation." Claude implicitly validates this by providing the review gate to catch contradictions. Gemini frames it as the transition from "stateless prompt-response loops to stateful, compounding knowledge architectures."

### The Solution: LLM-Wiki as a Compounding Knowledge Layer

All sources converge on the same architectural pattern: a persistent markdown wiki maintained by LLMs, sitting between raw multi-LLM research and agentic coding tools. Key properties:

1. **Persistent, not ephemeral** — contrasts with RAG, which re-processes the same documents on every query
2. **Compounding** — value increases with every ingest as cross-references, decisions, and contradictions accumulate
3. **Structured** — wikilinks, frontmatter, typed entities, decision records, contradiction flags
4. **LLM-maintained** — the wiki LLM (not a human) does the reading, writing, linking, and maintenance
5. **Human-reviewed** — a review gate with concrete quality criteria ensures signal before dev tool handoff

### The Pipeline: Multi-LLM Collection → Distillation → Dev Context

Claude's 4-phase architecture provides the high-level structure. Gemini's 7-phase model provides finer granularity. The distill-ingest methodology operationalizes the core distillation stages.

**Collection discipline:**
- Same 3–5 seed questions across all LLMs (control the variable)
- Force diverse angles: "core concepts, failure modes, best tools, non-obvious tradeoffs, recommended approach"
- Save raw immediately — never paste from memory
- Only multi-source for complex/architectural/long-lived topics; skip for simple one-offs
- Different LLMs have genuinely different knowledge distributions: Claude reasons better, GPT-4 has broader coverage, Gemini stronger on code

**Distillation methodology ([[multi-pass-distillation]]):**
1. Collect (20 min)
2. Filter (10 min) — 5-signal test: Specificity, Actionability, Non-obviousness, Consensus, Contradiction. Keep ≥3.
3. Distill (30 min) — synthesize surviving content. Conflicts become explicit tradeoffs.
4. Canonical (15 min) — dense markdown with frontmatter, facts, implementation code, tradeoffs table, ≥3 gotchas

**Quality gate:**
- Zero filler — every sentence states a specific fact
- All tools named with version
- Every tradeoff explicit
- Sources listed in frontmatter

**Context delivery ([[context-packs]]):**
- Per-module bundles: architecture, APIs, DB schema, constraints, conventions, implementation order
- Standardized exports: llms.txt (topic index), llms-full.txt (≤5MB flat dump), graph.jsonld (JSON-LD knowledge graph)
- Portable agent skills: SKILL.md packages in `~/.claude/skills/`
- Tool-specific integration: CLAUDE.md, .cursorrules, AGENTS.md, copilot-instructions.md

## Comparison Matrix

This table captures where the 9 sources diverge:

| Concept | ChatGPT (S1) | Claude (S2) | Gemini (S3) | Claude (S4) | Distill-Ingest (S5) | Others (S6-S9) |
|---------|-------------|-------------|-------------|-------------|---------------------|----------------|
| **Pipeline stages** | Raw → clustered → summarized → canonicalized | 4-phase: Collection → Wiki → Context → Dev | 7-phase: from Exploration to Closed-Loop | Python core: ingest → refine → synthesize → export | Collect → Filter → Distill → Canonical | — |
| **Dedup method** | Embedding clustering (OpenAI/VoyageAI/BGE) | — | Two-stage compiler (Stage 1 analysis) | SQLite dirty-only tracking | 5-signal manual scoring | — |
| **Contradiction handling** | — | UNRESOLVED flags | SUPERSEDED with archival | — | Conflict → Decision Space (design space framing) | — |
| **Context compression** | Research pipeline: 10K→20→2 pages | — | — | — | — | API-level: sliding window, summarization, truncation (doubao) |
| **Knowledge decay** | — | — | Ebbinghaus-weighted confidence | — | — | Memory consolidation/forgetting (doubao) |
| **Intent steering** | — | Implicit in schema | Explicit purpose.md | — | — | — |
| **Scaling** | — | — | — | — | — | Vector indexing at ~hundreds of pages (s2-notebooklm) |
| **Local LLM** | — | — | — | — | — | Ollama for background compilation (s2-notebooklm); "too slow" (S7) |
| **Web UI** | — | — | — | Open WebUI Pipelines | — | — |
| **MCP server** | — | — | Obsidian MCP | fastmcp with 5 tools | MCP for MemWeaver | — |

## Deep Analysis

### Epistemic Foundation

The most important insight across all sources is the reframing of LLM outputs. They are not raw data and not ground truth — they are **first-pass synthetic knowledge**. This means:
- ~80% is repetitive (differently phrased — requires semantic dedup, not exact match)
- Each model has inherent drift, hallucinated edges, and training bias
- The wiki distillation layer is where signal emerges from noise
- Disagreements between models define the design space, not errors to eliminate

This reframe justifies the entire wiki investment. Without it, the workflow looks like overhead. With it, the workflow is epistemically necessary.

### Two-Phase vs Multi-Phase Ingestion

There's a productive tension between Gemini's strict two-stage ingestion (analysis → generation) and the distill-ingest four-stage methodology (collect → filter → distill → canonical). They operate at different granularities:

- **Two-stage ingestion** (Gemini): controls the LLM's operational flow — don't let structure and content compete for attention
- **Four-stage methodology** (distill-ingest): controls the human's workflow — time-budgeted steps with explicit quality gates

Both are correct and complementary. The two-stage pattern governs how the LLM processes each source. The four-stage pattern governs how the human manages the overall research cycle.

### Context Compression as Moat

ChatGPT calls context compression "the real competitive moat" — and this is the most defensible claim in the research. Better models commoditize; better context engineering differentiates. The compression pipeline (10K pages → 20 pages → 2 pages → prompts) is the core value proposition.

The doubao source adds an important second level: API-call compression (sliding window, summarization, key info extraction, hard truncation). The research pipeline compresses what you know; the API level manages how you feed it to the LLM. Both are needed.

### Knowledge Lifecycle Management

Gemini provides the most sophisticated model: claims carry metadata (source, creation date, confidence), confidence decays exponentially (Ebbinghaus), contradictions trigger supersession with archival, and typed entities with semantic relationships enable graph traversal.

Distill-ingest operationalizes a simpler version: time-budgeted steps, quality gates, gotchas capture non-obvious issues. The doubao source adds memory consolidation (periodic compression of old conversations) and forgetting (pruning low-frequency history).

The pragmatic path: start with distill-ingest's methodology (simpler, immediately actionable), evolve toward Gemini's model as the wiki scales. The memory consolidation technique from doubao bridges the gap.

### Pipeline Operator Architecture

The pipeline operator (source 4) provides the concrete implementation architecture that all other sources call for abstractly. Key design decisions:
- **Shared core**: all interfaces (CLI, Web UI, MCP) call into `pipeline/runner.py` — no duplication
- **SQLite for state tracking**: dirty-only reprocessing avoids token waste
- **Build order**: core → CLI → MCP → Web UI (MCP before Web UI because it closes the Claude Code loop)
- **fastmcp as MCP library**: simpler than raw MCP SDK, ~50 lines for the server

## Recommendations

### Immediate (MVP)

1. **Build the pipeline core first** — Python module with ingest → refine → synthesize → export stages, SQLite run-state tracking, config.yaml for paths/model/schedule
2. **CLI interface** — argparse/typer with `--step`, `--watch`, `--dry-run` flags
3. **Enforce two-stage ingestion** — Stage 1 (read-only analysis) before Stage 2 (write pages). No exceptions.
4. **Apply the 5-signal filter** on every source — it's the cheapest quality lever
5. **Create `purpose.md`** — one-page project thesis read before every ingest

### Short-term (post-MVP)

6. **Add MCP server** (fastmcp) — `run_pipeline`, `get_article`, `list_articles`, `get_run_status`, `search_wiki`
7. **Set up Open WebUI Pipelines plugin** — `/run`, `/status`, `/preview` as chat commands
8. **Implement closed-loop harvesting** — start with Claude Code JSONL path scanning
9. **Add embedding-based semantic dedup** within Stage 1 analysis

### Medium-term

10. **Decay-weighted confidence scoring** — claim metadata with exponential decay
11. **Systematic supersession** — automatic stale→newer archival for contradictions
12. **Graph-layered entity extraction** — typed entities with semantic relationships
13. **Automated context pack generation** — per-module bundles and standardized exports

## Implementation Notes

### Tech Stack (from sources)

| Component | Technology | Source |
|-----------|-----------|--------|
| Pipeline core | Python 3.12, anthropic SDK, pydantic | S4 (cluade-pipeline-plan) |
| State tracking | SQLite3 (dirty-only reprocessing) | S4 |
| CLI | argparse or typer | S4 |
| Web UI | Open WebUI Pipelines plugin | S4 |
| MCP server | fastmcp | S4 |
| Local LLM | Ollama (background compilation only) | S9 (s2-notebooklm) |
| Vector/graph index | ChromaDB or SQLite/Neo4j (>hundreds of pages) | S9 |
| Obsidian integration | Obsidian MCP server (cyanheads/mcp-obsidian) | S3 (Gemini) |
| Embedding models | OpenAI/VoyageAI/BGE/Jina | S1 (ChatGPT) |

### Directory Structure

```
project/
├── purpose.md                    # Intent guidance (read every ingest)
├── CLAUDE.md                     # Schema + conventions (for Claude Code)
├── AGENTS.md                     # For OpenCode
├── .cursorrules                  # For Cursor
├── raw/
│   ├── llm/                      # LLM chat exports (immutable)
│   └── web/                      # Web article clips
├── wiki/
│   ├── sources/                  # Source summary pages
│   ├── concepts/                 # Cross-linked topic pages
│   ├── synthesis/                # Evolving thesis + export cycles
│   ├── index.md                  # Content catalog
│   └── log.md                    # Append-only timeline
├── pipeline/                     # Pipeline core
│   ├── config.yaml
│   ├── ingest.py
│   ├── refine.py
│   ├── synthesize.py
│   ├── export.py
│   └── runner.py
└── scripts/
    ├── run_pipeline.py           # CLI entry point
    └── scheduler.py              # Autonomous daemon (APScheduler)
```

### Build Order

```
Core (pipeline/) → CLI (scripts/) → MCP server (mcp_server/) → Web UI (open_webui/)
```

Each layer adds features without rewriting the core. The MCP server comes before Web UI because it closes the Claude Code loop: Claude generates wiki → MCP exposes it back → Claude references live wiki state.

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Wiki maintenance overhead kills momentum | Medium | High | Start with 80-min-per-topic budget (distill-ingest). Lint every 3–5 ingests. Weekly maintenance. |
| Hallucination amplification from multi-LLM sources | Medium | High | Never skip human review gate. Apply 5-signal filter. Cross-check claims across sources. |
| LLM token costs for frequent re-processing | Medium | Medium | Dirty-only reprocessing via SQLite. Local Ollama for background tasks. Batch ingests. |
| Context window limits on large wiki | Low | Medium | Hierarchical tree indexing (PageIndex) for long docs. Context packs scope per task. |
| Scope creep (building product vs solving problem) | Medium | High | MVP: CLI-only, no UI, no vector DB. Pipeline quality over features. |

## Open Questions for Further Research

1. **Seed question templates**: Should collection use stored prompt templates (topic → 5 seed questions auto-generated)? Could reduce collection time below 20 min.
2. **Supersession threshold**: When should contradictions auto-resolve (newer source overrides older) vs require human judgment? A confidence delta threshold?
3. **Confidence calibration**: How to normalize confidence scores across LLMs with different calibration curves? Claude tends to hedge; ChatGPT is more declarative.
4. **Chunking strategy for dedup**: What's the optimal chunk size and overlap for embedding-based dedup on LLM outputs (long-form analysis, not code)?
5. **Dev session harvesting sensitivity**: How to extract signal from noisy dev session logs without amplifying dead ends and debugging false starts?
6. **Graph query interface**: If typed entities with semantic relationships are implemented, what query language should coding agents use to traverse the knowledge graph?
7. **Multi-project knowledge transfer**: Can decision records and concepts from one project inform a related project's wiki cold start?
