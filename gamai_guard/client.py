"""Small client for the local GAMA Guard worker."""
from __future__ import annotations

import json
import urllib.error
import urllib.request


class GuardClient:
    def __init__(self, url: str = "http://127.0.0.1:18091", timeout: float = 120.0):
        self.url = url.rstrip("/")
        self.timeout = timeout

    def _req(self, path: str, body: dict | None = None) -> dict:
        data = None if body is None else json.dumps(body, ensure_ascii=False).encode()
        req = urllib.request.Request(
            self.url + path, data=data,
            headers={"Content-Type": "application/json"} if data else {})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as exc:
            raise RuntimeError("guard worker HTTP %s: %s" % (exc.code, exc.read()[:300])) from exc

    def health(self) -> dict:
        return self._req("/health")

    def stats(self) -> dict:
        return self._req("/stats")

    def check(self, text: str, tool: str = "answer") -> dict:
        return self._req("/check", {"text": text, "tool": tool})

    def check_many(self, texts: list[str], tool: str = "answer") -> list[dict]:
        return self._req("/check_many", {"texts": texts, "tool": tool})["results"]
