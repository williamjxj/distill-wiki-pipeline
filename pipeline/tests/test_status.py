from pipeline.wiki_core.status import get_pipeline_status
from test_lint import make_paths


def test_status_counts_pending_raw():
    status = get_pipeline_status(make_paths())
    assert status.pending_raw_count >= 1
    assert status.last_log_entry is None or isinstance(status.last_log_entry, str)
