from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


class ExportJobState(str, Enum):
    CREATED = "created"
    LINT_BLOCKED = "lint_blocked"
    DRAFT_DONE = "draft_done"
    COMPLETED = "completed"
    FAILED = "failed"


class JobState(str, Enum):
    CREATED = "created"
    ANALYSIS_DONE = "analysis_done"
    DRAFT_DONE = "draft_done"
    AWAITING_FINAL_CONFIRM = "awaiting_final_confirm"
    COMPLETED = "completed"
    FAILED = "failed"


_TERMINAL = {JobState.COMPLETED, JobState.FAILED}


@dataclass
class IngestJob:
    id: str
    raw_path: str
    state: JobState = JobState.CREATED
    analysis: str | None = None
    draft: str | None = None
    draft_payload: dict | None = None
    error: str | None = None
    raw_meta: dict = field(default_factory=dict)
    raw_body: str = ""


@dataclass
class ExportJob:
    id: str
    state: ExportJobState = ExportJobState.CREATED
    forced: bool = False
    lint_findings: list[dict] = field(default_factory=list)
    draft_body: str | None = None
    draft_meta: dict | None = None
    export_cycle: int | None = None
    sources_ingested: int | None = None
    prior_brief: str | None = None
    prior_brief_status: str | None = None
    prior_export_cycle: int | None = None
    error: str | None = None


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, IngestJob] = {}
        self._export_jobs: dict[str, ExportJob] = {}

    def get(self, job_id: str) -> IngestJob | None:
        return self._jobs.get(job_id)

    def active_ingest(self) -> IngestJob | None:
        for job in self._jobs.values():
            if job.state not in _TERMINAL:
                return job
        return None

    def create_ingest(self, raw_path: str) -> IngestJob:
        if self.active_ingest() is not None:
            raise ValueError("An ingest job is already active")
        job = IngestJob(id=str(uuid4()), raw_path=raw_path)
        self._jobs[job.id] = job
        return job

    def mark_failed(self, job: IngestJob, message: str) -> None:
        job.state = JobState.FAILED
        job.error = message

    def get_export(self, job_id: str) -> ExportJob | None:
        return self._export_jobs.get(job_id)

    def active_export(self) -> ExportJob | None:
        terminal = {ExportJobState.COMPLETED, ExportJobState.FAILED, ExportJobState.LINT_BLOCKED}
        for job in self._export_jobs.values():
            if job.state not in terminal:
                return job
        return None

    def create_export(self, force: bool = False) -> ExportJob:
        if self.active_export() is not None:
            raise ValueError("An export job is already active")
        job = ExportJob(id=str(uuid4()), forced=force)
        self._export_jobs[job.id] = job
        return job

    def mark_export_failed(self, job: ExportJob, message: str) -> None:
        job.state = ExportJobState.FAILED
        job.error = message

    def clear(self) -> None:
        self._jobs.clear()
        self._export_jobs.clear()


store = JobStore()
