# Experimental App

A testbed for the **LLM-Wiki research pipeline** — collect multi-LLM research, distill it into a compounding wiki, and sync synthesis into this repo for agentic development (Cursor, Claude Code, etc.).

Based on [Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f). See [`wiki/README.md`](wiki/README.md) for full wiki documentation.

## What this repo is

```
experimental-app/
├── docs/
│   ├── PROJECT_BRIEF.md      # synced synthesis for brainstorming / planning / implementation
│   └── RESEARCH_THESIS.md    # optional; running research view
├── scripts/
│   └── sync-wiki-docs.sh     # copy wiki exports → docs/
├── wiki/                     # project-wiki git submodule (research knowledge base)
└── src/                      # application code (future)
```

**North-star:** can a coding agent implement correctly from the exported context?

Research and building run in parallel — ingest, lint, and re-export as the project evolves. This is not a one-time handoff.

## Quick start

### Clone with submodule

```bash
git clone --recurse-submodules <repo-url>
# or, if already cloned:
git submodule update --init --recursive
```

### Research loop (in `wiki/`)

1. **Collect** — paste LLM chats into `wiki/raw/llm/` (kebab-case names, AGENTS.md frontmatter)
2. **Ingest** — `/wiki-ingest` one file at a time (Cursor skill in `wiki/.cursor/skills/`)
3. **Lint** — `/wiki-lint` after every 3–5 ingests
4. **Export** — `/wiki-export-brief` when ready for dev handoff
5. **Sync** — copy exports into this repo (see below)
6. **Build** — use `docs/PROJECT_BRIEF.md` with brainstorming, planning, and implementation skills

### Sync wiki → docs

After exporting (or updating) synthesis in the wiki submodule:

```bash
./scripts/sync-wiki-docs.sh              # PROJECT_BRIEF + RESEARCH_THESIS
./scripts/sync-wiki-docs.sh --brief-only # PROJECT_BRIEF only
```

Then commit both repos:

```bash
# wiki submodule first
cd wiki && git add -A && git commit -m "export brief cycle N" && cd ..

# parent repo
git add docs/ wiki
git commit -m "sync research synthesis"
```

## Wiki Pipeline Operator

For a local web UI and CLI to ingest, lint, export, and sync without Cursor:

- **Operator guide:** [`docs/WIKI_PIPELINE_OPERATOR.md`](docs/WIKI_PIPELINE_OPERATOR.md) — setup, CLI, MCP, cron
- **Design spec:** [`docs/superpowers/specs/2026-05-25-wiki-pipeline-operator-design.md`](docs/superpowers/specs/2026-05-25-wiki-pipeline-operator-design.md)

Quick start after setup (see operator guide):

```bash
./scripts/wiki-pipeline serve          # API on localhost:8787
cd pipeline/ui && npm run dev          # UI dev server
```

## Where to read what

| Document | Purpose |
|----------|---------|
| [`docs/WIKI_PIPELINE_OPERATOR.md`](docs/WIKI_PIPELINE_OPERATOR.md) | Pipeline operator setup, CLI, MCP, watch |
| [`docs/PROJECT_BRIEF.md`](docs/PROJECT_BRIEF.md) | Primary handoff — problem, approach, constraints, non-goals |
| [`docs/RESEARCH_THESIS.md`](docs/RESEARCH_THESIS.md) | Deeper running synthesis |
| [`wiki/AGENTS.md`](wiki/AGENTS.md) | Wiki schema, naming, ingest/export workflows |
| [`wiki/wiki/index.md`](wiki/wiki/index.md) | Catalog of sources and concepts |
| [`wiki/README.md`](wiki/README.md) | Submodule setup, Obsidian, skills, maintenance |

## Cursor skills (wiki submodule)

| Skill | Trigger |
|-------|---------|
| `wiki-ingest` | Process one raw source into the wiki |
| `wiki-lint` | Health-check contradictions, orphans, index sync |
| `wiki-export-brief` | Generate `project-brief.md` from synthesis |
| `wiki-query` | Ask questions against ingested research |

## Notes

- **Do not gitignore `wiki/`** in this repo — it is a tracked submodule.
- Raw LLM exports live in `wiki/raw/llm/`; rename to kebab-case **before** ingest.
- Approve exported briefs in the wiki (`status: current`) before treating `docs/PROJECT_BRIEF.md` as canonical.
