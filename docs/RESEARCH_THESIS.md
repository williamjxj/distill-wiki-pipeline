---
type: synthesis
status: evolving
last_updated: 2026-05-26
sources_ingested: 5
---

# Evolving Thesis

> Running synthesis across all ingested sources. Updated after every ingest.

## Current Understanding

This project implements Karpathy's **LLM-Wiki pattern** ([[wiki-vs-context-engine]]) as a multi-LLM research → distillation → dev-tool handoff pipeline. All three sources validate the core idea; ChatGPT's "context engine" reframe is product naming, not a different architecture.

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

### Thesis Delta ([[distill-ingest]])

Source 5 ([[distill-ingest]]) is a meta-document: it provides the rigorous distillation methodology that the earlier sources advocated for in principle. Key additions:

- **5-signal test** formalizes the [[multi-pass-distillation]] filter step: score every paragraph on Specificity, Actionability, Non-obviousness, Consensus, Contradiction — keep only 3+
- **Conflict → Decision Space** reframes [[contradictions-tracking]]: LLM disagreements define the design space, not bugs to eliminate
- **Distillation quality gate** adds concrete criteria to [[human-review-gate]]: zero filler, every tool versioned, tradeoffs explicit, ≥3 gotchas
- **Canonical file selection matrix** expands [[context-packs]] with tool-specific formats (CLAUDE.md, AGENTS.md, .cursorrules, llms.txt)
- **Meta-distillation** (LLM distilling LLMs) is a practical shortcut for the existing pipeline
- **4 tiers of automation** (no-code → agent-assisted → MCP → ETL) provides a maturity ladder for [[mvp-scope]]
- **Anti-pattern hall of fame** validates several existing design choices (one topic per file, annotation at collection time, git versioning)

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

- **Live Memory Layer**: Emphasize the integration of MCP server tools to make MemWeaver a live memory layer for IDEs, enhancing real-time access to relevant information (Concept: `mcp-server`).
- **Multi-LLM Workflow**: Highlight the importance of distilling insights from multiple LLMs into canonical files before ingestion (Concept: `distill-canonical` and `multi-llm-workflow`).

- **Context Handling Divergence**:
  - Web: Infinite, uncontrolled context accumulation.
  - API: Controlled, customizable context management (Details in [[llm-web-api-context-token-management]]).

- **Token Management**: Developers can set `max_tokens` and manage context through various intelligent techniques like summarization and data pruning (Further discussed in [[llm-web-api-context-token-management]])

Current Understanding:
- The analysis of `web/doubao.md` highlights the differences in context management between web dialogues and API calls, emphasizing the advantages of API calls for developers.

Open Questions:
- How can we effectively manage resources while maintaining user experience on both platforms?

Emerging Decisions:
- Continue exploring advanced memory management techniques for better resource utilization.

- **Current Understanding**: Emphasize the importance of distillation over raw log collection when dealing with complex or long-lived topics. Highlight that different LLMs offer unique insights which can be triangulated for more robust decisions.
- **Open Questions**: Explore how to streamline the multi-source collection and distillation process further, especially in real-world applications.
- **Emerging Decisions**: Recommend implementing an MCP server as part of the prompt harness to enhance MemWeaver's live memory layer functionality.
