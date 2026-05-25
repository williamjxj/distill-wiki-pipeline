from __future__ import annotations
import re
from pathlib import Path
import yaml

_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n?", re.DOTALL)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    meta = yaml.safe_load(match.group(1)) or {}
    body = text[match.end():]
    return meta, body


def read_markdown(path: Path) -> tuple[dict, str]:
    return parse_frontmatter(path.read_text(encoding="utf-8"))


def render_markdown(meta: dict, body: str) -> str:
    header = yaml.safe_dump(meta, sort_keys=False).strip()
    body = body.lstrip("\n")
    return f"---\n{header}\n---\n\n{body}"


def write_markdown(path: Path, meta: dict, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(meta, body), encoding="utf-8")


def write_frontmatter_field(path: Path, field: str, value) -> None:
    meta, body = read_markdown(path)
    meta[field] = value
    write_markdown(path, meta, body)


def list_raw_files(raw_dirs: list[Path]) -> list[Path]:
    files: list[Path] = []
    for directory in raw_dirs:
        if directory.is_dir():
            files.extend(sorted(directory.glob("*.md")))
    return files
