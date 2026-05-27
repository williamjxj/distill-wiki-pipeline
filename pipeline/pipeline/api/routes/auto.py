from __future__ import annotations

import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from pipeline.wiki_core.paths import resolve_paths
from pipeline.workflows.auto import stream_auto_pipeline

router = APIRouter(tags=["auto"])


async def _format_sse(file_spec: str):
    async for event in stream_auto_pipeline(file_spec, resolve_paths()):
        yield f"event: {event['event']}\ndata: {json.dumps(event)}\n\n"


@router.post("/auto")
async def run_auto(payload: dict):
    file_spec = payload.get("file", "all")
    return StreamingResponse(
        _format_sse(file_spec),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
