from __future__ import annotations
import subprocess
from dataclasses import dataclass
from pipeline.wiki_core.fs import read_markdown
from pipeline.wiki_core.paths import WikiPaths


@dataclass
class SyncResult:
    stdout: str
    warnings: list[str]


def run_sync(paths: WikiPaths, brief_only: bool = False) -> SyncResult:
    warnings: list[str] = []
    if paths.project_brief.is_file():
        meta, _ = read_markdown(paths.project_brief)
        if meta.get("status") == "draft":
            warnings.append("project-brief.md is still status: draft")

    cmd = [str(paths.sync_script)]
    if brief_only:
        cmd.append("--brief-only")

    proc = subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=paths.repo_root)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout or "sync failed")

    return SyncResult(stdout=proc.stdout.strip(), warnings=warnings)
