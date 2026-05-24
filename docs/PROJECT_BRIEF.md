---
type: project-brief
status: draft
date: 2026-05-24
export_cycle: 1
sources_ingested: 3
---

# Project Brief: Experimental App — LLM-Wiki Pipeline

## Problem

Engineers doing AI-assisted project research accumulate **context fragmentation** — scattered, duplicated, and contradictory inputs across ChatGPT, Claude, Gemini, docs, and notes. Coding agents (Cursor, Claude Code, etc.) fail from bad context, incomplete architecture, and conflicting instructions — not from model capability.

LLM chat exports are **synthetic first-pass knowledge**, not ground truth. Without a distillation layer, multi-LLM research amplifies noise and hallucinations rather than producing actionable signal.

## Current Understanding

This project implements Karpathy's **LLM-Wiki pattern** as a repeatable pipeline:

```
Multi-LLM collection → Wiki distillation → Human review → Dev context export → Agentic coding → (future) closed-loop harvest
```

Three research sources (ChatGPT, Gemini, Claude) all validate the core architecture. The wiki submodule (`wiki/`) is the **compounding knowledge layer** — a persistent markdown graph where contradictions are flagged, decisions recorded, and synthesis evolves across ingest cycles.

**North-star metric:** *Can Cursor implement this correctly?* ([[implementation-readiness]])

**Operational rhythm:**
- Collect identical prompts across LLMs → `raw/llm/`
- Ingest one source at a time (two-stage: analyze → write)
- Lint every 3–5 ingests
- Export brief when ready for dev-tool handoff
- Continue research until project complete — this is not a one-time handoff

See [[evolving-thesis]] and concept pages in `wiki/concepts/` for depth.

## Chosen Approach

### Firm decisions (high confidence)

| Area | Choice |
|------|--------|
| **Architecture** | LLM-Wiki compounding knowledge layer — markdown + git + wikilinks |
| **Naming** | "LLM-Wiki" over ChatGPT's "context engine" reframe (2:1 source consensus) |
| **Success metric** | Implementation readiness — dev context must enable correct agentic coding |
| **Ingest model** | Two-stage: structural analysis (no writes) → wiki generation; human confirms before marking ingested |
| **Distillation** | Multi-pass with lint gates between passes |
| **Contradictions** | Concept Divergence tables + wiki-lint; generate `contradictions.md` at export time from UNRESOLVED items |
| **Decision records** | decision + rationale + confidence + source attribution + runner-up + supersession status |
| **Dev handoff** | Targeted context packs via export-brief — never dump full wiki to coding agents |
| **Human gate** | Mandatory review before dev context export and after ingest |
| **Raw sources** | LLM chats in `raw/llm/` with AGENTS.md frontmatter; treat as synthetic sources |
| **Epistemic model** | Wiki distillation is where verified signal emerges from synthetic LLM outputs |

### Tentative decisions (medium confidence)

| Area | Lean | Notes |
|------|------|-------|
| **MVP scope** | Current project-wiki submodule pattern — manual ingest/lint/export skills, Obsidian as optional viewer | No custom app UI; automate incrementally |
| **Purpose steering** | Add `purpose.md` to parent project root; `AGENTS.md` handles schema | `docs/PROJECT_BRIEF.md` may evolve into purpose doc |
| **Context compression** | Per-task packs (Claude) as primary; tiered compression as design principle; `llms.txt`/Skills as optional later | |
| **Pipeline phases** | Claude's 4-phase model + Gemini's closed-loop harvest as Phase 5 | Phases 1–2 already operational manually |

### Deferred (post-MVP)

| Area | When |
|------|------|
| **Embedding-based dedup** | At scale — OpenAI/VoyageAI/BGE clustering (ChatGPT recommendation) |
| **Closed-loop harvesting** | After core ingest/export stable — Pratiyush llm-wiki adapters |
| **External tooling** | Evaluate OpenKB, Nashsu, obsidian-llm-wiki, qmd incrementally |
| **Knowledge graph (Neo4j)** | Not for v1 |
| **Custom FastAPI/LangChain pipeline** | ChatGPT's full-stack vision — defer until manual workflow proven |

## Constraints

- **Markdown + git only** for v1 — works with any dev toolchain
- **Human review non-negotiable** between wiki synthesis and dev-tool handoff
- **One source per ingest** — no batch processing
- **Raw body immutable** after ingest — only frontmatter `status` may change
- **Wiki submodule must stay tracked** in parent repo — never gitignore `wiki/`
- **Synthetic source awareness** — never treat LLM outputs as ground truth without distillation
- **Implementation readiness** — every export must answer "can an agent implement from this?"

## Non-Goals

- Building a custom web UI or "knowledge browser" (Obsidian is the viewer)
- Fully automated ingest-to-code pipeline without human gates
- Replacing dev tools — this system feeds Cursor/Claude Code, not substitutes them
- Commercial productization in v1 (noted as viable long-term by ChatGPT, not current scope)
- Ingesting Karpathy's original gist as a blocker — useful but not yet done
- Whole-wiki context dumps to coding agents
- Starting with Neo4j, vector DB, or embedding infrastructure

## Rejected Alternatives

| Alternative | Source | Why rejected |
|-------------|--------|--------------|
| **"Context Engine" instead of LLM-Wiki** | ChatGPT | Product naming, not architecture — 2:1 lean toward LLM-Wiki; compiling wiki is dynamic, not static |
| **Raw chat → Cursor directly** | All 3 | Causes hallucinated APIs, conflicting patterns, context pollution |
| **Ephemeral RAG per query** | Gemini | No compounding; token overhead; no analytical progress retained |
| **Single-pass ingest prompts** | Gemini | Fails on large transcripts; corrupts directories |
| **Embedding-only dedup (no LLM analysis)** | ChatGPT vs Gemini/Claude | Complementary, not exclusive — LLM analysis for MVP, embeddings post-MVP |
| **Fully automated distillation (no human gate)** | ChatGPT | Claude/Gemini consensus: human review before dev handoff is mandatory |
| **CLI-only with zero visual tooling** | ChatGPT | Obsidian as optional viewer is acceptable; "no UI" means no custom app |
| **Full wiki dump as dev context** | Claude | Targeted context packs per task/feature only |
| **Building "wiki" as static human encyclopedia** | ChatGPT | Mischaracterizes the compiling LLM-Wiki pattern |
| **Immediate closed-loop session harvesting** | Gemini | Post-MVP — core ingest/export first |

## Open Questions

These are intentional exploration areas — not blockers for starting implementation:

1. **When to add embedding-based dedup?** ChatGPT recommends early; Gemini/Claude rely on LLM analysis + lint for MVP. Trigger: wiki exceeds manual lint capacity or >N sources ingested.

2. **Which external tool to evaluate first?** Candidates: OpenKB (CLI + Skills export), Nashsu (visual clustering), Pratiyush (session sync), obsidian-llm-wiki (Obsidian plugin), qmd (BM25+vector search + MCP).

3. **How to harvest Cursor session logs?** Gemini documents adapter paths but no implementation yet. Pratiyush llm-wiki is the reference.

4. **Where should `purpose.md` live?** Parent root vs wiki submodule — lean parent root, but `docs/PROJECT_BRIEF.md` may subsume it after this export.

5. **Phase 3 compile automation?** Currently manual via export-brief skill. Prompt template vs script vs skill iteration — needs experimentation.

6. **Ingest Karpathy's original gist?** Would strengthen primary source attribution; current synthesis is from 3 LLM interpretations only.

7. **Contradictions surface format?** Concept Divergence tables vs dedicated `contradictions.md` — generate at export time for now, revisit if UNRESOLVED count grows.

---

*Export cycle 1 · 3 sources ingested · Draft pending approval*

Depth: [[research-to-implementation-pipeline]] · [[compounding-knowledge-layer]] · [[two-stage-ingestion]] · [[decision-records]] · [[context-packs]] · [[mvp-scope]]
