---
type: synthesis
status: evolving
last_updated: 2026-05-24
sources_ingested: 4
---

# Evolving Thesis

> Running synthesis across all ingested sources. Updated after every ingest.

## Current Understanding

This project implements Karpathy's **LLM-Wiki pattern** ([[wiki-vs-context-engine]]) as a multi-LLM research → distillation → dev-tool handoff pipeline. All four sources validate the core idea; ChatGPT's "context engine" reframe is product naming, not a different architecture.

**Problem:** [[context-fragmentation]] — scattered, duplicated, contradictory research across LLMs. Coding agents fail from bad context, not bad models.

**Epistemic reframe** ([[llm-outputs-as-synthetic-sources]]): LLM chat exports are first-pass synthetic knowledge, not ground truth. The wiki distillation layer is where signal emerges.

**Unified pipeline** ([[research-to-implementation-pipeline]]):
1. Multi-LLM collection with identical prompts → immutable `raw/llm/`
2. Wiki distillation via [[multi-pass-distillation]] → [[two-stage-ingestion]] + [[semantic-deduplication]] + [[contradictions-tracking]]
3. [[compounding-knowledge-layer]] — persistent markdown graph with [[decision-records]], cross-refs, supersession; steered by [[purpose-steering]]
4. [[human-review-gate]] → [[context-compression]] → compile [[context-packs]] (spec, architecture, tasks, AGENTS.md)
5. Dev tools (Cursor, Claude Code) via MCP / Skills / llms.txt
6. [[closed-loop-harvesting]] — dev session logs back to `raw/sessions/`

**Success criterion:** [[implementation-readiness]] — "Can Cursor implement this correctly?"

**Operational rhythm:** ingest one source at a time; lint every 3–5 ingests; export-brief for Phase 3 handoff; weekly maintenance.

**MVP** ([[mvp-scope]]): current project-wiki submodule pattern (markdown + git + Obsidian viewer). Add automation incrementally — OpenKB, embedding dedup, session harvesters are post-MVP.

## Open Questions

- When to add embedding-based dedup (ChatGPT) vs staying LLM-only for MVP?
- Which external tool to evaluate first: OpenKB, Nashsu, Pratiyush, obsidian-llm-wiki, qmd?
- How to implement [[closed-loop-harvesting]] for Cursor session logs?
- Should `purpose.md` live in parent project root or wiki submodule?
- Phase 3 compile automation — prompt template vs script vs export-brief skill?
- Karpathy's original gist not yet ingested as primary source — worth adding?

## Emerging Decisions

| Topic | Lean | Confidence | Sources |
|-------|------|------------|---------|
| Architecture | LLM-Wiki [[compounding-knowledge-layer]] | **high** | all 3 |
| Naming | LLM-Wiki over "context engine" ([[wiki-vs-context-engine]]) | high | Claude + Gemini |
| North-star | [[implementation-readiness]] | high | all 3 |
| Ingest model | [[two-stage-ingestion]] + human confirm | high | all 3 |
| Distillation | [[multi-pass-distillation]] with lint gates | high | all 3 |
| Contradictions | [[contradictions-tracking]] via Divergence tables + lint | high | all 3 |
| Decision records | [[decision-records]] with source + runner-up | high | ChatGPT + Claude |
| Compression | [[context-compression]] → targeted [[context-packs]] | high | all 3 |
| Dev handoff | export-brief, not full wiki dump | high | Claude + ChatGPT |
| Human gate | [[human-review-gate]] before dev context export | high | Claude + Gemini |
| Purpose | [[purpose-steering]] via root purpose.md | medium | Gemini + Claude |
| MVP scope | Markdown wiki submodule, Obsidian viewer, manual skills | medium | all 3 |
| Closed loop | Post-MVP session harvesting | medium | Gemini |
| Embedding dedup | Post-MVP at scale | low | ChatGPT |

## Update (2026-05-25 ingest: claude pipeline plan)

[[2026-05-25-cluade-pipeline-plan|Claude's implementation plan]] converges on **shared pipeline core + three adapters** (UI, automation, MCP) — matching our v2 architecture. Key fork: Claude recommends Open WebUI Pipelines; we shipped a **purpose-built operator** with Ollama (`qwen2.5:7b-instruct`) and human approval gates. MCP is read-heavy sidecar, not primary UI backend.
