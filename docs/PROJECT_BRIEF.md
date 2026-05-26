---
type: project-brief
status: current
date: '2026-05-26'
export_cycle: 3
sources_ingested: 8
---

# Project Brief: LLM-Wiki Handoff Pipeline

## Problem

The problem addressed by this project is **context fragmentation** in AI-assisted engineering, where engineers face scattered, duplicated, and contradictory inputs from various sources like ChatGPT, Claude, Gemini, Reddit, GitHub, PDFs, and more. This context fragmentation leads to incomplete architecture, conflicting instructions, and ultimately, agent failure during implementation.

## Current Understanding

- **Evolving Thesis:** The project implements Karpathy's LLM-Wiki pattern as a multi-LLM research → distillation → dev-tool handoff pipeline.
- **Key Concepts:**
  - **Problem:** Context fragmentation is the biggest challenge in AI-assisted engineering.
  - **Solution:** A compounding knowledge layer (wikis) directly addresses this issue by avoiding feeding raw contradictory transcripts to development agents.
  - **Epistemic Framing:** LLM outputs are treated as synthetic first-pass knowledge, and wiki distillation is where truth emerges.

## Chosen Approach

- **Unified Pipeline:**
  1. **Multi-LLM Collection:** Collect data from multiple LLMs with identical prompts → immutable `raw/llm/`.
  2. **Wiki Distillation:** Use multi-pass distillation to clean and integrate data into a persistent markdown graph.
  3. **Compounding Knowledge Layer:** Build a dynamic, AI-maintained knowledge base that avoids context pollution.
  4. **Human Review Gate:** Ensure the synthesized knowledge is free of contradictions and ready for dev tools.
  5. **Dev Tools Handoff:** Export compendiums like `AGENTS.md`, architecture documents, tasks lists, etc., to guide development.
  6. **Closed-Loop Harvesting:** Use developer session logs to keep the wiki evergreen.

## Constraints

- The project must handle context fragmentation effectively by avoiding raw contradictory transcripts.
- All LLM outputs are treated as synthetic first-pass knowledge that requires distillation and verification.
- Dev tools need scoped, compressed context bundles for implementation readiness rather than full wikis or raw research dumps.

## Non-Goals

- **No Raw Data Dump:** Do not directly feed raw LLM outputs to dev agents; they must be distilled and verified through human review.
- **No Static Human Wiki:** Avoid treating the wiki as a static, manually organized resource. It should be AI-maintained and compounding knowledge.

## Rejected Alternatives

- **Context Engine vs. Wiki:** ChatGPT suggests evolving to a "context engine" rather than a traditional wiki, but this does not change the core architecture.
- **Embedding Dedup Early:** Delay embedding-based deduplication until MVP for resource management reasons.
- **Open WebUI Pipelines:** Claude's recommendation of Open WebUI Pipelines is seen as an optional acceleration layer and not a core requirement.

## Open Questions

- When to add embedding-based dedup (ChatGPT) vs staying LLM-only for MVP?
- Which external tool to evaluate first: OpenKB, Nashsu, Pratiyush, obsidian-llm-wiki, qmd?
- How to implement closed-loop harvesting for Cursor session logs?
- Should `purpose.md` live in the parent project root or wiki submodule?
- Phase 3 compile automation — prompt template vs script vs export-brief skill?
- Karpathy's original gist not yet ingested as primary source — worth adding?

## Chosen Approach

- **LLM-Wiki Naming:** Adopt LLM-Wiki naming and structure.
- **Five Stage Distillation Pipeline:** Implement a five-stage pipeline (raw → clustered → summarized → canonicalized → implementation-oriented).
- **Human Review Gate:** Mandatory human review before exporting to dev tools.
- **Context Compressed Packs:** Targeted context packs for each task, not the full wiki.

By addressing these constraints and open questions, we ensure a robust and effective handoff pipeline that leverages AI in a structured manner.