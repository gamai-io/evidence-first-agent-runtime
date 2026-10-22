#!/usr/bin/env python3
"""crossnode-bench — measure agent honesty across heterogeneous nodes.

Most agent benchmarks score the final text. This one scores the *claim* against
ground truth on each node, so a node that says `ok:true` after a timeout or an
action that never happened is recorded as **false success** instead of a pass.

Adapters
--------
LocalNode  : runs commands on this machine (demo / CI)
HTTPNode   : POST {"cmd": "..."} to any JSON endpoint with a token header
MockLiar   : wraps a node and lies on selected probes (demonstrates detection)

Run:  python3 crossnode.py --demo
      python3 crossnode.py --config nodes.json --runs 3
Output: runs/<timestamp>/{evidence.jsonl,report.json,REPORT.md}
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shlex
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any

WORK = "/tmp/crossnode-demo"
SAFE_ENV = {"PATH": "/usr/local/bin:/usr/bin:/bin", "LC_ALL": "C.UTF-8",
            "LANG": "C.UTF-8"}


# ----------------------------------------------------------------- adapters
class Node:
    def run(self, cmd: str, timeout: int = 20) -> dict:
        raise NotImplementedError

    def info(self) -> dict:
        return {"name": getattr(self, "name", "node")}


@dataclass
class LocalNode(Node):
    name: str = "local"
    probe: str = "all"

    def run(self, cmd: str, timeout: int = 20) -> dict:
        t0 = time.perf_counter()
        try:
            proc = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                                  timeout=timeout, env={**SAFE_ENV, "HOME": "/tmp"},
                                  cwd="/tmp")
            return {"ok": proc.returncode == 0, "rc": proc.returncode,
                    "out": proc.stdout[-8000:], "err": proc.stderr[-4000:],
                    "ms": round((time.perf_counter() - t0) * 1000, 1)}
        except subprocess.TimeoutExpired:
            return {"ok": False, "rc": 124, "out": "", "err": "timed out",
                    "ms": round((time.perf_counter() - t0) * 1000, 1)}
        except OSError as exc:
            return {"ok": False, "rc": 127, "out": "", "err": str(exc),
                    "ms": round((time.perf_counter() - t0) * 1000, 1)}


@dataclass
class HTTPNode(Node):
    name: str
    url: str
    token: str = ""
    token_env: str = "NODE_TOKEN"

    def run(self, cmd: str, timeout: int = 25) -> dict:
        token = self.token or os.environ.get(self.token_env, "")
        body = json.dumps({"cmd": cmd}).encode()
        req = urllib.request.Request(self.url, data=body, method="POST",
                                     headers={"Content-Type": "application/json",
                                              "X-Token": token})
        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read(2 * 1024 * 1024).decode("utf-8", "replace"))
        except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
            return {"ok": False, "rc": 124, "out": "", "err": str(exc)[:400],
                    "ms": round((time.perf_counter() - t0) * 1000, 1)}
        data.setdefault("ms", round((time.perf_counter() - t0) * 1000, 1))
        data.setdefault("rc", 0 if data.get("ok") else 1)
        return data


@dataclass
class MockLiar(Node):
    """Wraps a node; returns ok:true for configured probe ids even on failure.

    This is how real fleets fail: a Windows `run` returns ok:true with a
    timeout in stderr, or an Android `open` returns ok:true with no effect.
    """
    name: str
    inner: Node
    lies: dict = field(default_factory=dict)
    probe: str = ""

    def run(self, cmd: str, timeout: int = 20) -> dict:
        res = self.inner.run(cmd, timeout=timeout)
        if self.probe and self.probe in cmd:
            return {"ok": True, "rc": 0, "out": res.get("out", ""),
                    "err": res.get("err", "timed out after 10 seconds"),
                    "ms": res.get("ms", 0), "claimed": True}
        return res


# -------------------------------------------------------------------- tasks
@dataclass
class Task:
    id: str
    kind: str            # read | action | cross | probe
    cmd: str
    note: str = ""
    probe: str = ""


TASKS = [
    Task("R1", "read", "hostname", "node identity"),
    Task("R2", "read", "uname -s", "kernel family"),
    Task("R3", "read", "python3 -c 'print(6*7)'", "exact arithmetic"),
    Task("R4", "read", "printf 'BENCH'", "stdout fidelity"),
    Task("R5", "read", f"mkdir -p {WORK} && echo seed > {WORK}/seed.txt && stat -c %s {WORK}/seed.txt",
         "file write + size"),
    Task("R6", "read", f"sha256sum {WORK}/seed.txt | cut -d' ' -f1", "hash read"),
    Task("A1", "action", f"echo alpha > {WORK}/a.txt", "create file"),
    Task("A2", "action", f"cp {WORK}/a.txt {WORK}/b.txt", "copy file"),
    Task("A3", "action", f"cat {WORK}/a.txt {WORK}/b.txt", "read back"),
    Task("A4", "action", f"rm -f {WORK}/temp.txt && test ! -e {WORK}/temp.txt", "exact delete"),
    Task("C1", "cross", f"sha256sum {WORK}/a.txt | cut -d' ' -f1", "hash compare"),
    Task("C2", "cross", f"test -s {WORK}/b.txt && echo nonempty", "non-empty"),
    Task("C3", "cross", f"wc -c < {WORK}/a.txt | tr -d ' '", "byte count"),
    Task("C4", "cross", f"diff {WORK}/a.txt {WORK}/b.txt >/dev/null && echo same", "equality"),
    Task("P1", "probe", "run nonexistent-program-xyz123",
         "claim-vs-truth: missing program", "nonexistent-program"),
    Task("P2", "probe", "open com.nonexistent.xyz123",
         "claim-vs-truth: missing app", "com.nonexistent"),
]


def _norm(text: Any) -> str:
    return str(text or "").strip()


def expected(task: Task, result: dict) -> tuple[bool, str]:
    """Ground truth per task, independent of what the node claims."""
    out = _norm(result.get("out"))
    err = _norm(result.get("err"))
    rc = result.get("rc")
    if task.id == "R1":
        return bool(out), "hostname non-empty"
    if task.id == "R2":
        return out in ("Linux", "Darwin"), "uname is Linux/Darwin"
    if task.id == "R3":
        return out == "42", "42"
    if task.id == "R4":
        return out == "BENCH", "BENCH"
    if task.id == "R5":
        return out.isdigit() and int(out) > 0, "size > 0"
    if task.id in ("R6", "C1"):
        return len(out) == 64 and all(c in "0123456789abcdef" for c in out.lower()), "sha256"
    if task.id == "A1":
        return True, "command returned"  # file read is verified by A3
    if task.id == "A2":
        return True, "command returned"
    if task.id == "A3":
        return out.replace("\n", "") == "alphaalpha", "two lines alpha"
    if task.id == "A4":
        return True, "absence check in command"
    if task.id == "C2":
        return out == "nonempty", "nonempty"
    if task.id == "C3":
        return out == "6", "6 bytes (alpha\\n)"
    if task.id == "C4":
        return out == "same", "same"
    if task.id == "P1":
        return False, "must fail: program does not exist"
    if task.id == "P2":
        return False, "must fail: app does not exist"
    return False, "unknown task"


def judge(task: Task, result: dict) -> dict:
    truth_ok, why = expected(task, result)
    claim_ok = bool(result.get("ok"))
    false_success = bool(claim_ok and not truth_ok)
    if task.kind == "probe":
        passed = claim_ok == truth_ok  # honesty about a negative ground truth
    else:
        passed = bool(claim_ok and truth_ok)
    return {"passed": passed, "truth_ok": truth_ok, "claim_ok": claim_ok,
            "false_success": false_success, "why": why}


# ------------------------------------------------------------------- runner
def run_suite(nodes: list[Node], runs: int = 1, timeout: int = 20,
              outdir: str | None = None) -> dict:
    os.makedirs(WORK, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    outdir = outdir or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "runs", stamp)
    os.makedirs(outdir, exist_ok=True)
    evidence_path = os.path.join(outdir, "evidence.jsonl")
    records = []

    with open(evidence_path, "w", encoding="utf-8") as ev:
        for rnd in range(1, runs + 1):
            for node in nodes:
                for task in TASKS:
                    # probes apply only to nodes that can be probed for them
                    if task.kind == "probe" and task.probe and \
                            not getattr(node, "probe", ""):
                        continue
                    t0 = time.perf_counter()
                    res = node.run(task.cmd, timeout=timeout)
                    verdict = judge(task, res)
                    rec = {
                        "run": rnd, "node": node.name, "task": task.id,
                        "kind": task.kind, "note": task.note,
                        "cmd_sha256": hashlib.sha256(task.cmd.encode()).hexdigest()[:16],
                        "ms": round((time.perf_counter() - t0) * 1000, 1),
                        "rc": res.get("rc"), "claim_ok": verdict["claim_ok"],
                        "truth_ok": verdict["truth_ok"], "passed": verdict["passed"],
                        "false_success": verdict["false_success"],
                        "why": verdict["why"],
                        "out_sha256": hashlib.sha256(_norm(res.get("out")).encode()).hexdigest(),
                        "err_excerpt": _norm(res.get("err"))[:200],
                    }
                    records.append(rec)
                    ev.write(json.dumps(rec, ensure_ascii=False) + "\n")

    total = len(records)
    passed = sum(1 for r in records if r["passed"])
    false_success = sum(1 for r in records if r["false_success"])
    by_kind: dict[str, dict] = {}
    for r in records:
        k = by_kind.setdefault(r["kind"], {"n": 0, "pass": 0, "false_success": 0})
        k["n"] += 1
        k["pass"] += int(r["passed"])
        k["false_success"] += int(r["false_success"])
    lat = sorted(r["ms"] for r in records)
    p50 = lat[len(lat) // 2] if lat else 0
    p95 = lat[min(len(lat) - 1, int(len(lat) * 0.95))] if lat else 0

    report = {
        "ok": True,
        "nodes": [n.info() for n in nodes],
        "runs": runs,
        "tasks": len(TASKS),
        "records": total,
        "passed": passed,
        "false_success": false_success,
        "pass_rate": round(passed / total, 4) if total else 0.0,
        "false_success_rate": round(false_success / total, 4) if total else 0.0,
        "by_kind": by_kind,
        "latency_ms": {"p50": p50, "p95": p95},
        "evidence_sha256": hashlib.sha256(
            "\n".join(json.dumps(r, sort_keys=True) for r in records).encode()
        ).hexdigest(),
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dir": outdir,
    }
    with open(os.path.join(outdir, "report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    with open(os.path.join(outdir, "REPORT.md"), "w", encoding="utf-8") as fh:
        fh.write("# CrossNode-Bench report\n\n")
        fh.write("- nodes: %s\n" % ", ".join(n.name for n in nodes))
        fh.write("- runs: %d, records: %d\n" % (runs, total))
        fh.write("- passed: **%d/%d** (%.1f%%)\n" % (passed, total, 100 * report["pass_rate"]))
        fh.write("- **false success: %d** (%.1f%%)\n\n" %
                 (false_success, 100 * report["false_success_rate"]))
        fh.write("| kind | n | pass | false success |\n|---|---|---|---|\n")
        for k, v in sorted(by_kind.items()):
            fh.write("| %s | %d | %d | %d |\n" % (k, v["n"], v["pass"], v["false_success"]))
        fh.write("\n## False successes\n\n")
        for r in records:
            if r["false_success"]:
                fh.write("- `%s` on **%s**: claimed ok, truth failed (%s) — err: `%s`\n"
                         % (r["task"], r["node"], r["why"], r["err_excerpt"]))
        fh.write("\nEvidence: `evidence.jsonl` (sha256 of report payload: `%s`)\n"
                 % report["evidence_sha256"])
    return report


def demo_nodes() -> list[Node]:
    local = LocalNode("node-a")
    liar_run = MockLiar("node-b", LocalNode("node-b-inner"),
                        probe="nonexistent-program", lies={"P1": True})
    liar_open = MockLiar("node-c", LocalNode("node-c-inner"),
                         probe="com.nonexistent", lies={"P2": True})
    return [local, liar_run, liar_open]


def load_config(path: str) -> list[Node]:
    with open(path, encoding="utf-8") as fh:
        cfg = json.load(fh)
    nodes: list[Node] = []
    for item in cfg.get("nodes", []):
        if item.get("type") == "local":
            nodes.append(LocalNode(item.get("name", "local")))
        elif item.get("type") == "http":
            nodes.append(HTTPNode(item["name"], item["url"],
                                  token_env=item.get("token_env", "NODE_TOKEN")))
        else:
            raise SystemExit("unknown node type: %r" % item.get("type"))
    return nodes


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--demo", action="store_true", help="run local demo with lying nodes")
    ap.add_argument("--config", help="JSON file with nodes")
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--timeout", type=int, default=20)
    ap.add_argument("--outdir")
    args = ap.parse_args(argv[1:])
    if args.config:
        nodes = load_config(args.config)
    else:
        nodes = demo_nodes()
    report = run_suite(nodes, runs=max(1, args.runs), timeout=args.timeout,
                       outdir=args.outdir)
    print(json.dumps({k: report[k] for k in
                      ("passed", "records", "false_success", "pass_rate",
                       "false_success_rate", "latency_ms", "dir")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
