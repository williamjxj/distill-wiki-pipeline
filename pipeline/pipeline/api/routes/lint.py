from fastapi import APIRouter
from pipeline.wiki_core.lint import run_lint
from pipeline.wiki_core.models import LintFinding
from pipeline.wiki_core.paths import resolve_paths

router = APIRouter(tags=["lint"])


def _finding_to_dict(finding: LintFinding) -> dict:
    data = finding.__dict__.copy()
    data["severity"] = finding.severity.value
    return data


@router.get("/lint")
def get_lint():
    findings = run_lint(resolve_paths())
    return {"findings": [_finding_to_dict(f) for f in findings]}
