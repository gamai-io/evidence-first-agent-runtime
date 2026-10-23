"""Planning: Vultr Serverless Inference first, deterministic planner as fallback.

The planner only proposes shell steps that run inside the sandbox. Every step is
still filtered by the pre-execution guard, so a bad plan cannot escape.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass

DEFAULT_BASE = os.environ.get("VULTR_INFERENCE_BASE", "https://api.vultrinference.com/v1")
DEFAULT_MODEL = os.environ.get("VULTR_MODEL", "llama-3.1-70b-instruct")

SYSTEM = (
    "You are a sandbox operator. You plan short shell pipelines that run inside "
    "an isolated container with a writable /work directory and no network. "
    "Answer with JSON only: {\"steps\":[{\"cmd\":\"...\",\"why\":\"...\"}]}. "
    "Maximum 5 steps. Never delete data, never touch network, never escalate."
)


@dataclass
class Step:
    cmd: str
    why: str = ""


class VultrInference:
    name = "vultr-inference"

    def __init__(self, api_key: str | None = None, model: str | None = None, base: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("VULTR_INFERENCE_KEY", "")
        self.model = model or DEFAULT_MODEL
        self.base = (base or DEFAULT_BASE).rstrip("/")

    def available(self) -> bool:
        return bool(self.api_key)

    def chat(self, messages: list[dict], max_tokens: int = 700, timeout: float = 45.0) -> str:
        if not self.available():
            raise RuntimeError("VULTR_INFERENCE_KEY not set")
        body = json.dumps({"model": self.model, "messages": messages, "max_tokens": max_tokens, "temperature": 0.2}).encode()
        req = urllib.request.Request(
            f"{self.base}/chat/completions",
            data=body,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        return payload["choices"][0]["message"]["content"]


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?|\n?```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        raise ValueError("no JSON object in model output")
    return json.loads(match.group(0))


def deterministic_plan(task: str) -> list[Step]:
    lower = task.lower()
    seed = [
        Step("mkdir -p /work && cd /work && printf 'alpha\\n' > a.txt && head -c 4096 /dev/urandom > big.bin && head -c 1024 /dev/urandom > mid.bin", "seed sample workspace"),
        Step("cd /work && find . -type f -printf '%s %p\\n' | sort -rn | head -3", "list three largest files"),
        Step("cd /work && find . -type f -printf '%s %p\\n' | sort -rn | head -3 | while read sz p; do h=$(sha256sum \"$p\" | cut -d' ' -f1); echo \"$p,$sz,$h\"; done > report.csv && cat report.csv", "hash the three largest files into report.csv"),
    ]
    if any(k in lower for k in ("sha", "hash", "najve", "largest", "fajl", "file", "csv")):
        return seed
    return [Step("cd /work && pwd && ls -la", "inspect empty workspace")]


def plan(task: str, llm: VultrInference | None = None) -> tuple[list[Step], str]:
    if llm is not None and llm.available():
        try:
            raw = llm.chat([{"role": "system", "content": SYSTEM}, {"role": "user", "content": task}])
            data = _extract_json(raw)
            steps = [Step(str(s.get("cmd", "")).strip(), str(s.get("why", ""))) for s in data.get("steps", []) if s.get("cmd")]
            steps = [s for s in steps if s.cmd][:5]
            if steps:
                return steps, f"{llm.name}:{llm.model}"
        except (urllib.error.URLError, TimeoutError, RuntimeError, ValueError, KeyError):
            pass
    return deterministic_plan(task), "deterministic"
