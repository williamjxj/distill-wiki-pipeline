from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from pipeline.wiki_core.fs import write_markdown
from pipeline.wiki_core.paths import resolve_paths

router = APIRouter(tags=["upload"])

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

_LLM_TYPES = {"llm-chat"}
_WEB_TYPES = {"web-article"}
_VALID_TYPES = _LLM_TYPES | _WEB_TYPES
_VALID_SOURCES = {"claude", "chatgpt", "gemini", "web"}


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "untitled"


def _validate_date(value: str) -> None:
    if not _DATE_RE.match(value):
        raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="date must be a valid calendar date") from exc


def _validate_frontmatter(
    *,
    raw_type: str,
    source: str,
    topic: str,
    raw_date: str,
    question: str | None,
    url: str | None,
) -> dict:
    if raw_type not in _VALID_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"type must be one of: {', '.join(sorted(_VALID_TYPES))}",
        )
    if source not in _VALID_SOURCES:
        raise HTTPException(
            status_code=400,
            detail=f"source must be one of: {', '.join(sorted(_VALID_SOURCES))}",
        )
    if not topic.strip():
        raise HTTPException(status_code=400, detail="topic is required")
    _validate_date(raw_date)

    meta: dict = {
        "type": raw_type,
        "source": source,
        "topic": topic.strip(),
        "date": raw_date,
        "status": "pending",
    }

    if raw_type in _LLM_TYPES:
        if not question or not question.strip():
            raise HTTPException(status_code=400, detail="question is required for llm-chat")
        meta["question"] = question.strip()
    elif raw_type in _WEB_TYPES:
        if not url or not url.strip():
            raise HTTPException(status_code=400, detail="url is required for web-article")
        meta["url"] = url.strip()

    return meta


def _target_filename(
    *,
    raw_type: str,
    source: str,
    topic: str,
    raw_date: str,
    upload_name: str,
) -> str:
    if raw_type in _LLM_TYPES:
        topic_slug = _slugify(topic)
        return f"{raw_date}-{source}-{topic_slug}.md"

    stem = Path(upload_name).stem
    slug = _slugify(stem) if stem else _slugify(topic)
    if not _SLUG_RE.match(slug):
        slug = _slugify(topic)
    return f"{slug}.md"


@router.post("/raw/upload")
async def upload_raw(
    file: UploadFile = File(...),
    type: str = Form(...),
    source: str = Form(...),
    topic: str = Form(...),
    date: str = Form(...),
    question: str | None = Form(None),
    url: str | None = Form(None),
):
    paths = resolve_paths()
    meta = _validate_frontmatter(
        raw_type=type,
        source=source,
        topic=topic,
        raw_date=date,
        question=question,
        url=url,
    )

    body_bytes = await file.read()
    try:
        body = body_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="file must be UTF-8 text") from exc

    filename = _target_filename(
        raw_type=type,
        source=source,
        topic=topic,
        raw_date=date,
        upload_name=file.filename or "upload.md",
    )
    target_dir = paths.raw_llm if type in _LLM_TYPES else paths.raw_web
    target_path = target_dir / filename

    if target_path.exists():
        raise HTTPException(status_code=409, detail=f"file already exists: {filename}")

    write_markdown(target_path, meta, body)
    rel_path = target_path.relative_to(paths.wiki_root)
    return {"path": str(rel_path), "meta": meta}
