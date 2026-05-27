# Auto Pipeline UI — Design Spec

**Date:** 2026-05-26
**Status:** Draft
**Export Cycle:** N/A

## Goal

Add a one-click "Auto Pipeline" mode to the React operator dashboard that runs the full ingest→lint→export→lint→graph→sync pipeline as a single operation, complementing the existing step-by-step workflow.

## Approach

**Dedicated nav page** with SSE-based real-time progress streaming. User selects target files (specific pending file or "All Pending") and clicks one button. The page shows a step-by-step progress tracker with live logs and a final summary.

## Backend: SSE `/api/auto` endpoint

### Route

```
POST /api/auto
Content-Type: application/json

{"file": "raw/llm/2026-05-25-claude-test.md"}
// or
{"file": "all"}
```

"all" processes every file with `status: pending` sequentially (same behavior as `wiki-pipeline auto --all`). If there are no pending files, the endpoint immediately returns an error result rather than running.

Response is `text/event-stream`. The EventSource protocol uses named events:

| Event | Payload | When |
|-------|---------|------|
| `step` | `{"step": "frontmatter", "status": "running", "message": "..."}` | Start of a step |
| `step` | `{"step": "frontmatter", "status": "done", "message": "..."}` | Step succeeded |
| `step` | `{"step": "frontmatter", "status": "failed", "message": "..."}` | Step failed |
| `log` | `{"line": "some output text..."}` | Arbitrary log output |
| `result` | `{"status": "completed"|"failed", "summary": {"files_processed": int, "errors": int, "warnings": int}}` | Pipeline finished |

### Steps

1. **frontmatter** — `_ensure_frontmatter()` for each target file
2. **ingest** — `ingest_workflow` per file (same as CLI auto)
3. **lint** — `run_lint()`
4. **export** — `export_workflow`
5. **lint** — `run_lint()` again (post-export)
6. **graph** — `build_graph()`
7. **sync** — `run_sync()`

### Implementation

Refactor `pipeline/workflows/auto.py` from a single synchronous function into a generator that yields event dicts:

```python
def run_auto_pipeline(paths, file_spec) -> Generator[dict, None, dict]:
    # yields {"event": "step", ...} and {"event": "log", ...} messages
    # final return is the result dict
```

Both the CLI and the new SSE endpoint consume this generator. The CLI just prints each message; the API wraps it in SSE framing.

No new dependencies — Python's `StreamingResponse` from FastAPI handles SSE natively with `async def` + `async for`.

## Frontend: AutoPipeline page

### Nav placement

New nav link **Auto Pipeline** inserted between Export and Lint:

```
Dashboard | Raw Queue | Ingest | Export | Auto Pipeline | Lint | Graph | Log
```

### Page layout

```
┌─────────────────────────────────────────────────────┐
│ Auto Pipeline                        [target ▼] [▶] │
├─────────────────────────────────────────────────────┤
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  │
│  │ FM   │→ │Ingest│→ │ Lint │→ │Export│→ │ Lint │… │
│  │ done✓│  │  ▶   │  │      │  │      │  │      │   │
│  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘  │
├─────────────────────────────────────────────────────┤
│ [log output area — scrollable <pre> block]          │
│ Injecting frontmatter for chat.md...                │
│ ✓ Frontmatter injected                              │
│ Ingesting raw/llm/chat.md...                        │
│ ✓ Ingest complete                                   │
│ Running lint...                                      │
│ 2 warnings found                                    │
│ ...                                                  │
├─────────────────────────────────────────────────────┤
│ Pipeline completed — 1 file processed, 0 errors     │
└─────────────────────────────────────────────────────┘
```

### States

| State | Behavior |
|-------|----------|
Optionally, the page includes a file drop zone at the top. Files dropped there are uploaded via the existing `POST /api/raw/upload` endpoint, then immediately run through the auto pipeline. This gives users a true single-flow experience without needing to pre-upload via the Raw Queue page.

### States

| State | Behavior |
|-------|----------|
| **Idle** | File drop zone + file selector ("All Pending" + individual files), Run button enabled, stepper all-grey, log area shows placeholder |
| **No pending files** | File selector shows "No pending files" (disabled), Run button disabled, a note explaining the user can upload raw files via the drop zone or Raw Queue page |
| **Running** | File selector disabled, Run button shows "Running…" + spinner, stepper shows progress, log area streams live |
| **Completed** | Green result banner with file count / error count / warning count, Run button re-enabled, stepper shows final state |
| **Failed** | Red result banner with error detail, Run button re-enabled, stepper shows which step failed |
| **Completed** | Green result banner with file count / error count / warning count, Run button re-enabled, stepper shows final state |
| **Failed** | Red result banner with error detail, Run button re-enabled, stepper shows which step failed |

### Components

New file: `pipeline/ui/src/pages/AutoPipeline.tsx` (+ `AutoPipeline.module.css`)

- Uses `EventSource` or `fetch` with `ReadableStream` to consume SSE — `fetch` is preferred since `EventSource` doesn't support POST. Use the streaming fetch pattern with `response.body.getReader()`.
- On mount, fetches pending files to populate the dropdown.
- Tracks step states in a `Map<StepName, StepState>` for the stepper.
- Auto-scrolls the log panel to bottom as new lines arrive.

### API additions

New export in `pipeline/ui/src/api.ts`:

```typescript
export function runAutoPipeline(file: string): Promise<Response> {
  return fetch(`${API_BASE}/api/auto`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ file }),
  });
}
```

The caller reads the response body as a stream.

## Existing code to modify

| File | Change |
|------|--------|
| `pipeline/workflows/auto.py` | Refactor into generator yielding event dicts |
| `pipeline/api/routes/` | New `auto.py` router with POST `/api/auto` SSE endpoint |
| `pipeline/api/main.py` | Register new router |
| `pipeline/ui/src/App.tsx` | Add nav link + route for Auto Pipeline |
| `pipeline/ui/src/pages/` | New `AutoPipeline.tsx` + `AutoPipeline.module.css` |
| `pipeline/ui/src/api.ts` | Add `runAutoPipeline()` function |

## Out of scope

- The existing step-by-step pages are untouched
- No new CLI commands (the existing `wiki-pipeline auto` continues to work)
- No YAML formatter or "distill" as new pipeline stages — those are the existing frontmatter injection and ingest steps
