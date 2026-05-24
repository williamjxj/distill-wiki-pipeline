#!/usr/bin/env bash
# Sync wiki synthesis exports into parent docs/.
# Run from repo root: ./scripts/sync-wiki-docs.sh [--brief-only]

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WIKI_SYNTH="$ROOT/wiki/wiki/synthesis"
DOCS="$ROOT/docs"

BRIEF_SRC="$WIKI_SYNTH/project-brief.md"
THESIS_SRC="$WIKI_SYNTH/evolving-thesis.md"
BRIEF_DST="$DOCS/PROJECT_BRIEF.md"
THESIS_DST="$DOCS/RESEARCH_THESIS.md"

brief_only=false
if [[ "${1:-}" == "--brief-only" ]]; then
  brief_only=true
elif [[ -n "${1:-}" ]]; then
  echo "Usage: $0 [--brief-only]" >&2
  exit 1
fi

if [[ ! -f "$BRIEF_SRC" ]]; then
  echo "error: missing $BRIEF_SRC (run /wiki-export-brief first)" >&2
  exit 1
fi

mkdir -p "$DOCS"
cp "$BRIEF_SRC" "$BRIEF_DST"
echo "synced: wiki/wiki/synthesis/project-brief.md → docs/PROJECT_BRIEF.md"

if grep -q '^status: draft' "$BRIEF_SRC"; then
  echo "note: project-brief.md is still status: draft — approve in wiki before treating as current"
fi

if [[ "$brief_only" == false ]]; then
  if [[ ! -f "$THESIS_SRC" ]]; then
    echo "error: missing $THESIS_SRC" >&2
    exit 1
  fi
  cp "$THESIS_SRC" "$THESIS_DST"
  echo "synced: wiki/wiki/synthesis/evolving-thesis.md → docs/RESEARCH_THESIS.md"
fi
