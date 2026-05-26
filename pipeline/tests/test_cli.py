from __future__ import annotations

from pipeline.cli.main import serve


def test_serve_runs_without_reload(monkeypatch):
    calls: list[dict[str, object]] = []

    def fake_run(app: str, **kwargs):
        calls.append({"app": app, **kwargs})

    monkeypatch.setattr("uvicorn.run", fake_run)

    serve(host="0.0.0.0", port=9999)

    assert calls == [
        {
            "app": "pipeline.api.main:app",
            "host": "0.0.0.0",
            "port": 9999,
            "reload": False,
        }
    ]