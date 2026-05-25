from __future__ import annotations

import platform
import subprocess
import sys
import time

from pipeline.wiki_core.paths import resolve_paths
from pipeline.wiki_core.status import get_pipeline_status


def _notify_pending(count: int) -> None:
    message = f"{count} pending raw file(s)"
    if platform.system() == "Darwin":
        subprocess.run(
            [
                "osascript",
                "-e",
                f'display notification "{message}" with title "Wiki Pipeline"',
            ],
            check=False,
        )
    else:
        print(f"Wiki Pipeline: {message}", file=sys.stdout, flush=True)


def watch_loop(interval: int = 60) -> None:
    seen = 0
    while True:
        count = get_pipeline_status(resolve_paths()).pending_raw_count
        if count > 0 and count != seen:
            _notify_pending(count)
            seen = count
        time.sleep(interval)
