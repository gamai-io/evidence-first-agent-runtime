#!/usr/bin/env python3
"""Local HTTP worker for the GAMA Guard text cascade.

Endpoints (localhost by default):
  GET  /health
  GET  /stats
  POST /check       {"text": "...", "tool": "answer"}
  POST /check_many  {"texts": ["..."], "tool": "answer"}

The worker owns one Cascade, one lock and one prototype/text cache. It is
deliberately single-process: bge-m3 batches are serialized on one GPU.
"""
from __future__ import annotations

import argparse
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from gamai_guard.text import Cascade

_lock = threading.Lock()
_started = time.time()
_stats = {"requests": 0, "texts": 0, "last_ms": None}
_cascade: Cascade | None = None


def cascade() -> Cascade:
    global _cascade
    if _cascade is None:
        _cascade = Cascade(EMBED_URL, MODEL, THRESHOLD)
    return _cascade


def _json(handler: BaseHTTPRequestHandler, code: int, obj: dict) -> None:
    body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class Handler(BaseHTTPRequestHandler):
    server_version = "GAMAGuard/1.0"

    def log_message(self, fmt: str, *args) -> None:
        print("%s - %s" % (self.address_string(), fmt % args), flush=True)

    def do_GET(self) -> None:
        if self.path == "/health":
            c = cascade()
            _json(self, 200, {
                "ok": True,
                "model": MODEL,
                "embed_url": EMBED_URL,
                "threshold": THRESHOLD,
                "prototype_classes": len(c._vectors() or {}),
                "text_cache": len(c._text_cache),
                "uptime_s": round(time.time() - _started, 1),
            })
        elif self.path == "/stats":
            _json(self, 200, {"ok": True, **_stats})
        else:
            _json(self, 404, {"ok": False, "error": "not found"})

    def do_POST(self) -> None:
        try:
            n = int(self.headers.get("Content-Length", "0"))
            if n <= 0 or n > 2_000_000:
                raise ValueError("bad content length")
            body = json.loads(self.rfile.read(n).decode("utf-8"))
        except Exception as exc:
            _json(self, 400, {"ok": False, "error": str(exc)})
            return
        if self.path == "/check":
            text = body.get("text")
            if not isinstance(text, str):
                _json(self, 400, {"ok": False, "error": "text required"})
                return
            out = self._run([text], body.get("tool", "answer"))
            _json(self, 200, {"ok": True, **out[0]})
        elif self.path == "/check_many":
            texts = body.get("texts")
            if not isinstance(texts, list) or not all(isinstance(x, str) for x in texts):
                _json(self, 400, {"ok": False, "error": "texts must be a list of strings"})
                return
            _json(self, 200, {"ok": True, "results": self._run(texts, body.get("tool", "answer"))})
        else:
            _json(self, 404, {"ok": False, "error": "not found"})

    def _run(self, texts: list[str], tool: str) -> list[dict]:
        t0 = time.perf_counter()
        with _lock:
            out = cascade().check_many(texts, tool=tool)
        ms = round((time.perf_counter() - t0) * 1000, 1)
        _stats["requests"] += 1
        _stats["texts"] += len(texts)
        _stats["last_ms"] = ms
        return [{**r, "ms": ms} for r in out]


def main() -> int:
    global EMBED_URL, MODEL, THRESHOLD
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8091)
    ap.add_argument("--embed-url", default="http://127.0.0.1:11434/api/embed")
    ap.add_argument("--model", default="bge-m3")
    ap.add_argument("--threshold", type=float, default=0.15)
    a = ap.parse_args()
    EMBED_URL, MODEL, THRESHOLD = a.embed_url, a.model, a.threshold
    srv = ThreadingHTTPServer((a.host, a.port), Handler)
    print("gama-guard worker on http://%s:%d model=%s" % (a.host, a.port, MODEL), flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
