# Wiki Pipeline UI

Phase 1 React dashboard for pipeline status, raw queue, log viewing, and sync.

## Development

Run the UI and API in separate terminals:

```bash
cd pipeline/ui && npm install && npm run dev
# separate terminal: ./scripts/wiki-pipeline serve
```

The UI dev server runs on http://127.0.0.1:5173 and talks to the FastAPI backend at http://127.0.0.1:8787 (override with `VITE_API_BASE`).

## Build

```bash
npm run build
```
