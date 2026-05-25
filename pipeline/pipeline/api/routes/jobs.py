from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from pipeline.api.jobs import ExportJobState, JobState, store
from pipeline.llm.workflows import export as export_workflow
from pipeline.llm.workflows import ingest as ingest_workflow
from pipeline.wiki_core.paths import resolve_paths

router = APIRouter(tags=["jobs"])


class StartIngestRequest(BaseModel):
    raw_path: str


class ApproveDraftRequest(BaseModel):
    edits: dict | None = None


class StartExportRequest(BaseModel):
    force: bool = False


def _job_response(job) -> dict:
    return {
        "id": job.id,
        "raw_path": job.raw_path,
        "state": job.state.value,
        "analysis": job.analysis,
        "draft": job.draft,
        "draft_payload": job.draft_payload,
        "error": job.error,
    }


def _export_job_response(job) -> dict:
    return {
        "id": job.id,
        "state": job.state.value,
        "forced": job.forced,
        "lint_findings": job.lint_findings,
        "draft_body": job.draft_body,
        "draft_meta": job.draft_meta,
        "export_cycle": job.export_cycle,
        "sources_ingested": job.sources_ingested,
        "prior_brief": job.prior_brief,
        "prior_brief_status": job.prior_brief_status,
        "prior_export_cycle": job.prior_export_cycle,
        "error": job.error,
    }


@router.post("/jobs/ingest")
async def start_ingest(body: StartIngestRequest):
    try:
        job = await ingest_workflow.start_ingest_job(store, body.raw_path)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        job = store.get(store.active_ingest().id) if store.active_ingest() else None
        if job and job.state == JobState.FAILED:
            raise HTTPException(status_code=500, detail=job.error or str(exc)) from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _job_response(job)


@router.post("/jobs/ingest/{job_id}/approve-analysis")
async def approve_analysis(job_id: str):
    try:
        job = await ingest_workflow.approve_analysis(store, job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        job = store.get(job_id)
        if job and job.state == JobState.FAILED:
            raise HTTPException(status_code=500, detail=job.error or str(exc)) from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _job_response(job)


@router.post("/jobs/ingest/{job_id}/approve-draft")
def approve_draft(job_id: str, body: ApproveDraftRequest | None = None):
    edits = body.edits if body else None
    try:
        job = ingest_workflow.approve_draft(store, job_id, edits)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _job_response(job)


@router.post("/jobs/ingest/{job_id}/confirm")
def confirm_ingest(job_id: str):
    try:
        job = ingest_workflow.confirm_ingest(store, job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        job = store.get(job_id)
        if job and job.state == JobState.FAILED:
            raise HTTPException(status_code=500, detail=job.error or str(exc)) from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _job_response(job)


@router.get("/jobs/ingest/{job_id}")
def get_ingest_job(job_id: str):
    job = store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return _job_response(job)


@router.post("/jobs/export")
async def start_export(body: StartExportRequest | None = None):
    force = body.force if body else False
    try:
        job = await export_workflow.start_export(store, force=force)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        job = store.active_export()
        if job and job.state == ExportJobState.FAILED:
            raise HTTPException(status_code=500, detail=job.error or str(exc)) from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _export_job_response(job)


@router.post("/jobs/export/{job_id}/approve")
def approve_export(job_id: str):
    try:
        job = export_workflow.approve_export(store, job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        job = store.get_export(job_id)
        if job and job.state == ExportJobState.FAILED:
            raise HTTPException(status_code=500, detail=job.error or str(exc)) from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _export_job_response(job)


@router.get("/jobs/export/{job_id}")
def get_export_job(job_id: str):
    job = store.get_export(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return _export_job_response(job)
