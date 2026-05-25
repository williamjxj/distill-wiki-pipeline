from __future__ import annotations

import httpx

from pipeline.wiki_core.paths import load_config


async def complete_ollama(system: str, user: str, task: str = "ingest") -> str:
    cfg = load_config()
    base = cfg["llm"]["ollama_base_url"].rstrip("/")
    model = cfg["llm"]["models"]["ollama"]
    override = cfg["llm"].get("overrides", {}).get(task)
    if override and override != "ollama":
        raise NotImplementedError(f"Provider {override} not implemented yet")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
    }
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(f"{base}/api/chat", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["message"]["content"]
