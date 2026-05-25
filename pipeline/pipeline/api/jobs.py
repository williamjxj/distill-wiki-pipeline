from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


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


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, IngestJob] = {}

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

    def clear(self) -> None:
        self._jobs.clear()


store = JobStore()
