"""The agent loop: guard, plan, execute in a sandbox, verify, publish evidence."""

from __future__ import annotations

import importlib.util
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from . import guard, llm
from .evidence import Ledger
from .executor import ExecResult, Executor, pick_executor

ROOT = Path(__file__).resolve().parents[1]


def _load_proofgate():
    path = ROOT / "proofgate" / "proofgate.py"
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location("gama_proofgate", path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PROOFGATE = _load_proofgate()


@dataclass
class StepResult:
    index: int
    cmd: str
    why: str
    verdict: dict
    result: ExecResult | None
    confirmed: bool

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "cmd": self.cmd,
            "why": self.why,
            "verdict": self.verdict,
            "exec": self.result.to_dict() if self.result else None,
            "confirmed": self.confirmed,
        }


@dataclass
class Run:
    id: str
    task: str
    planner: str = ""
    executor: dict = field(default_factory=dict)
    steps: list[StepResult] = field(default_factory=list)
    refusal: dict | None = None
    started: float = field(default_factory=time.time)
    finished: float = 0.0
    report: dict = field(default_factory=dict)

    def to_dict(self, ledger: Ledger | None = None) -> dict:
        return {
            "id": self.id,
            "task": self.task,
            "planner": self.planner,
            "executor": self.executor,
            "steps": [s.to_dict() for s in self.steps],
            "refusal": self.refusal,
            "duration_ms": int(((self.finished or time.time()) - self.started) * 1000),
            "report": self.report,
            "ledger": ledger.to_dict() if ledger else None,
        }


Emitter = Callable[[dict], None]


class Agent:
    def __init__(self, executor: Executor | None = None, planner: llm.VultrInference | None = None) -> None:
        self.executor = executor or pick_executor()
        self.planner = planner or llm.VultrInference()

    def run(self, task: str, emit: Emitter | None = None) -> tuple[Run, Ledger]:
        emit = emit or (lambda _e: None)
        run = Run(id=uuid.uuid4().hex[:12], task=task, executor=self.executor.info())
        ledger = Ledger(run.id)
        ledger.append("task", "accepted", {"task": task}, True, {"executor": run.executor})
        emit({"type": "task", "id": run.id, "task": task, "executor": run.executor})

        task_verdict = guard.check_task(task)
        ledger.append("guard", "task", {"task": task}, task_verdict.allowed, task_verdict.to_dict())
        emit({"type": "guard", "stage": "task", "verdict": task_verdict.to_dict()})
        if not task_verdict.allowed:
            run.refusal = {"stage": "task", **task_verdict.to_dict()}
            run.finished = time.time()
            run.report = {"ok": False, "status": "refused", "reason": task_verdict.reason}
            emit({"type": "done", **run.report})
            return run, ledger

        steps, planner_name = llm.plan(task, self.planner)
        run.planner = planner_name
        ledger.append("plan", "steps", {"count": len(steps)}, True, {"planner": planner_name})
        emit({"type": "plan", "planner": planner_name, "steps": [{"cmd": s.cmd, "why": s.why} for s in steps]})

        claims: list[dict] = []
        for index, step in enumerate(steps, start=1):
            verdict = guard.check_command(step.cmd)
            ledger.append("guard", "command", {"cmd": step.cmd}, verdict.allowed, verdict.to_dict())
            emit({"type": "guard", "stage": "command", "index": index, "verdict": verdict.to_dict()})
            if not verdict.allowed:
                run.refusal = {"stage": "command", "index": index, **verdict.to_dict()}
                ledger.append("refusal", step.cmd, {}, False, verdict.to_dict())
                emit({"type": "refusal", "cmd": step.cmd, "reason": verdict.reason})
                break

            emit({"type": "step", "index": index, "cmd": step.cmd, "state": "running"})
            result = self.executor.run(step.cmd)
            confirmed = result.ok
            claims.append({
                "text": f"step {index} exit code is zero",
                "predicate": "rc_zero",
                "observed": result.rc,
            })
            ledger.append("exec", step.cmd, {"why": step.why}, confirmed, result.to_dict())
            run.steps.append(StepResult(index, step.cmd, step.why, verdict.to_dict(), result, confirmed))
            emit({"type": "step", "index": index, "cmd": step.cmd, "state": "done", "confirmed": confirmed, "exec": result.to_dict()})
            if not confirmed:
                break

        if run.refusal is None and PROOFGATE is not None and claims:
            run.report = PROOFGATE.check(claims)
        elif run.refusal is not None:
            run.report = {"ok": False, "status": "refused", "reason": run.refusal.get("reason")}
        else:
            run.report = {"ok": bool(run.steps) and all(s.confirmed for s in run.steps), "status": "unverified"}

        run.finished = time.time()
        ledger.append("report", "evidence", {}, bool(run.report.get("ok")), run.report)
        emit({"type": "ledger", "verify": ledger.verify(), "head": ledger.head})
        emit({"type": "done", **run.report, "steps": len(run.steps)})
        return run, ledger
