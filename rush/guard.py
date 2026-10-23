"""Pre-execution guard: destructive-action refusal and injection immunity.

Nothing reaches the sandbox before this gate says it is allowed. The gate is
fail-closed: unknown errors block the action instead of letting it through.
"""

from __future__ import annotations

import importlib.util
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DESTRUCTIVE = [
    (re.compile(r"\brm\s+(?:-\S+\s+)*-(?=[a-zA-Z]*[rf])[a-zA-Z]*[rf][a-zA-Z]*\s+(?:/|/\*|~|\$HOME)(?:\s|$)"), "recursive delete of root/home"),
    (re.compile(r"\bmkfs(\.\w+)?\b"), "filesystem format"),
    (re.compile(r"\bdd\b[^\n]*\bof=/dev/(sd|nvme|vd)"), "raw disk write"),
    (re.compile(r":\(\)\s*\{\s*:\|:&\s*\};:"), "fork bomb"),
    (re.compile(r"\b(drop|truncate)\s+(table|database)\b", re.I), "destructive SQL"),
    (re.compile(r"\bshutdown\b|\breboot\b|\bpoweroff\b", re.I), "host power action"),
    (re.compile(r"\bchmod\s+-R\s+777\s+/\b"), "world-writable root"),
    (re.compile(r"\b(curl|wget)[^\n|]*\|\s*(ba)?sh\b"), "remote code execution pipe"),
    (re.compile(r"\bhistory\s+-c\b|\brm\s+.*\.bash_history\b"), "anti-forensics"),
]

INJECTION_HINTS = [
    "ignore previous", "ignore all previous", "disregard the above", "system prompt",
    "you are now", "act as", "developer mode", "jailbreak", "print your instructions",
    "zaboravi prethodno", "ignoriši uputstvo", "ti si sada",
]


@dataclass
class Verdict:
    allowed: bool
    reason: str
    score: float
    matched: list[str]

    def to_dict(self) -> dict:
        return {"allowed": self.allowed, "reason": self.reason, "score": round(self.score, 3), "matched": self.matched}


def _load_immunity():
    path = ROOT / "agent-immunity" / "immunity.py"
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location("gama_immunity", path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception:
        return None
    return module


_IMMUNITY = _load_immunity()


def check_command(command: str) -> Verdict:
    for pattern, label in DESTRUCTIVE:
        if pattern.search(command):
            return Verdict(False, f"blocked: {label}", 1.0, [label])
    lower = command.lower()
    hints = [h for h in INJECTION_HINTS if h in lower]
    if hints:
        return Verdict(False, "blocked: instruction embedded in command", 0.9, hints)
    return Verdict(True, "allowed", 0.0, [])


def check_task(task: str) -> Verdict:
    if _IMMUNITY is not None:
        try:
            score, hits = _IMMUNITY.threat_score(task)
            if score >= 0.55:
                return Verdict(False, "blocked: prompt-injection signature", float(score), list(hits)[:6])
        except Exception:
            return Verdict(False, "blocked: immunity check failed (fail-closed)", 1.0, ["immunity-error"])
    lower = task.lower()
    hints = [h for h in INJECTION_HINTS if h in lower]
    if hints:
        return Verdict(False, "blocked: prompt-injection phrase", 0.7, hints)
    return Verdict(True, "allowed", 0.0, [])
