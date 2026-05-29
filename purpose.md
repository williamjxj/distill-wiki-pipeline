# Purpose: Distill-Wiki-Pipeline

> Read this before every ingest cycle to maintain focus and prevent scope drift.

## Thesis

Multi-LLM outputs contain genuine signal buried in noise, repetition, and contradiction. The only way to extract that signal is through structured distillation into a persistent, cross-linked, version-controlled knowledge base. This wiki is that distillation layer — sitting between raw multi-LLM research and agentic coding tools.

## Engineering Goals

1. **Compounding knowledge**: every ingest should make the wiki more valuable — more cross-references, more decisions, more resolved contradictions — not just larger
2. **Implementation-grade context**: synthesis exports must be sufficient for a coding agent (Cursor, Claude Code, OpenCode) to implement correctly without additional research — "Can Cursor implement this correctly?" is the north star
3. **Tool-agnostic portability**: all content is markdown + git; no lock-in to any specific editor, LLM provider, or platform
4. **Repeatable methodology**: multi-LLM collection with seed questions, two-stage ingestion, multi-pass distillation — not ad-hoc pasting
5. **Closed-loop verification**: discrepancies between planned architecture and generated code must be harvested back into the wiki for re-ingestion

## Core Constraints

- CLI-first, UI secondary (MVP is terminal-based)
- Local-first — no external hosting, no cloud dependencies
- Content is immutable after ingest (raw layer) — only frontmatter status changes
- LLM outputs are synthetic knowledge, not ground truth — human review gate required
- Pipeline quality over feature scope — dirty-only reprocessing, no wasteful full re-runs

## Research Boundary

**In scope:** multi-LLM distillation methodology, knowledge graph maintenance, context compression, dev tool integration, closed-loop harvesting

**Out of scope:** vector databases (deferred until >hundreds of pages), automated LLM API collection (manual paste for now), multi-user features, commercial product packaging

## Status

Latest export: cycle 4 (9 sources, 18 concepts) — May 29, 2026
