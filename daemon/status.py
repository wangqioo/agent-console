from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any


PROVIDERS = {
    "claude": {
        "status_url": "https://status.claude.com/api/v2/status.json",
        "summary_url": "https://status.claude.com/api/v2/summary.json",
    },
    "openai": {
        "status_url": "https://status.openai.com/api/v2/status.json",
        "summary_url": "https://status.openai.com/api/v2/summary.json",
    },
}


def _fetch_json(url: str, timeout: float = 8.0) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "agent-console/0.1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def get_provider_status() -> dict[str, Any]:
    providers: dict[str, Any] = {}

    for name, config in PROVIDERS.items():
        try:
            data = _fetch_json(config["status_url"])
            status = data.get("status", {})
            providers[name] = {
                "ok": True,
                "indicator": status.get("indicator"),
                "description": status.get("description"),
                "source": config["status_url"],
            }
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            providers[name] = {
                "ok": False,
                "error": str(exc),
                "source": config["status_url"],
            }

    return {"providers": providers}
