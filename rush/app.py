"""FastAPI surface: one page, one endpoint, live evidence stream."""

from __future__ import annotations

import asyncio
import json
import queue
import threading
import uuid
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel

from .agent import Agent
from .executor import DockerExecutor, pick_executor

STATIC = Path(__file__).parent / "static"
app = FastAPI(title="gamAI Rush — Blast Radius Zero", version="0.1.0")

RUNS: dict[str, dict] = {}


class TaskIn(BaseModel):
    task: str


def _new_executor():
    base = pick_executor()
    if isinstance(base, DockerExecutor):
        return DockerExecutor(
            image=base.image,
            memory=base.memory,
            pids_limit=base.pids_limit,
            cpus=base.cpus,
            volume=f"rush_{uuid.uuid4().hex[:10]}",
        )
    return base


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    return HTMLResponse((STATIC / "index.html").read_text(encoding="utf-8"))


@app.get("/health")
def health() -> dict:
    ex = pick_executor()
    return {"ok": True, "executor": ex.info()}


@app.post("/api/run")
def run(payload: TaskIn) -> JSONResponse:
    executor = _new_executor()
    agent = Agent(executor=executor)
    run_obj, ledger = agent.run(payload.task)
    RUNS[run_obj.id] = run_obj.to_dict(ledger)
    if hasattr(executor, "cleanup"):
        executor.cleanup()
    body = run_obj.to_dict(ledger)
    body["ledger"] = {"verify": ledger.verify(), "head": ledger.head, "count": len(ledger.records)}
    return JSONResponse(body)


@app.get("/api/run/stream")
async def stream(task: str) -> StreamingResponse:
    events: queue.Queue = queue.Queue()
    holder: dict = {}

    def worker() -> None:
        executor = _new_executor()
        agent = Agent(executor=executor)
        try:
            run_obj, ledger = agent.run(task, emit=events.put)
            holder["run"] = run_obj.to_dict(ledger)
            holder["ledger"] = {"verify": ledger.verify(), "head": ledger.head, "count": len(ledger.records)}
            RUNS[run_obj.id] = holder["run"]
        except Exception as exc:  # fail-closed: surface the error as an event
            events.put({"type": "error", "error": f"{type(exc).__name__}: {exc}"})
        finally:
            if hasattr(executor, "cleanup"):
                executor.cleanup()
            events.put(None)

    threading.Thread(target=worker, daemon=True).start()

    async def gen():
        loop = asyncio.get_running_loop()
        while True:
            item = await loop.run_in_executor(None, events.get)
            if item is None:
                if "ledger" in holder:
                    yield "data: " + json.dumps({"type": "final", **holder}) + "\n\n"
                yield "data: " + json.dumps({"type": "end"}) + "\n\n"
                break
            yield "data: " + json.dumps(item, ensure_ascii=False) + "\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")
