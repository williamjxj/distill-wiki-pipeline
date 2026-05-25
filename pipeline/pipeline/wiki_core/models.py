from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class LintFinding:
    severity: Severity
    code: str
    message: str
    path: str | None = None


@dataclass
class RawFile:
    path: str
    status: str
    topic: str | None
    source: str | None
    date: str | None


@dataclass
class PipelineStatus:
    pending_raw_count: int
    pending_raw_files: list[RawFile]
    lint_error_count: int
    lint_warning_count: int
    export_cycle: int | None
    brief_status: str | None
    last_log_entry: str | None
