#!/usr/bin/env python3
"""Scale test for CrossNode-Bench: 1,000 distinct tasks, 5 nodes.

This is a **scale/regression** test, not an independent fleet validation.
It reuses the real LocalNode adapter and MockLiar wrappers, and writes the
same evidence JSONL shape. Replace nodes with HTTPNode entries for a real
heterogeneous run.

  python3 scale1000.py
  python3 scale1000.py --runs 1 --out runs/scale1000
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from dataclasses import dataclass

from crossnode import LocalNode, MockLiar, _norm


@dataclass
class STask:
    id: str
    kind: str
    cmd: str
    expected: str
    probe: bool = False


def tasks() -> list[STask]:
    out: list[STask] = []
    for i in range(700):
        out.append(STask(f"R{i:04d}", "read", f"printf 'OK-{i:04d}'", f"OK-{i:04d}"))
    for i in range(150):
        out.append(STask(f"A{i:04d}", "action", f"printf 'ACT-{i:04d}\\n'", f"ACT-{i:04d}"))
    for i in range(100):
        out.append(STask(f"C{i:04d}", "cross", f"printf 'CROSS-{i:04d}'", f"CROSS-{i:04d}"))
    for i in range(50):
        # probes must fail; a lying node claims success.
        out.append(STask(f"P{i:04d}", "probe", f"run nonexistent-scale-{i:04d}", "",
                         probe=True))
    assert len(out) == 1000
    return out


def judge(t: STask, res: dict) -> dict:
    claim = bool(res.get("ok"))
    out = _norm(res.get("out"))
    if t.probe:
        truth = not claim
        passed = truth
        false_success = claim and not truth
        why = "probe must fail" if false_success else "probe honestly failed"
        return {"claim_ok": claim, "truth_ok": truth, "passed": passed,
                "false_success": false_success, "why": why}
    truth = out == t.expected
    passed = claim and truth
    false_success = claim and not truth
    why = "expected stdout" if passed else ("claim without expected stdout" if false_success else "failed")
    return {"claim_ok": claim, "truth_ok": truth, "passed": passed,
            "false_success": false_success, "why": why}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="")
    ap.add_argument("--runs", type=int, default=1)
    args = ap.parse_args()
    ts = time.strftime("%Y%m%d-%H%M%S")
    outdir = args.out or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "runs", f"scale1000-{ts}")
    os.makedirs(outdir, exist_ok=True)
    nodes = [
        LocalNode("node-a"),
        LocalNode("node-b"),
        MockLiar("node-c", LocalNode("node-c-inner"), probe="nonexistent-scale-0000"),
        MockLiar("node-d", LocalNode("node-d-inner"), probe="nonexistent-scale-0001"),
        MockLiar("node-e", LocalNode("node-e-inner"), probe="nonexistent-scale-0002"),
    ]
    all_tasks = tasks()
    records = []
    evp = os.path.join(outdir, "evidence.jsonl")
    t0 = time.perf_counter()
    with open(evp, "w", encoding="utf-8") as ev:
        for rnd in range(1, args.runs + 1):
            for node in nodes:
                for t in all_tasks:
                    res = node.run(t.cmd, timeout=10)
                    v = judge(t, res)
                    rec = {"run": rnd, "node": node.name, "task": t.id,
                           "kind": t.kind, "cmd_sha256": hashlib.sha256(t.cmd.encode()).hexdigest()[:16],
                           "ms": res.get("ms", 0), "rc": res.get("rc"),
                           "claim_ok": v["claim_ok"], "truth_ok": v["truth_ok"],
                           "passed": v["passed"], "false_success": v["false_success"],
                           "why": v["why"],
                           "out_sha256": hashlib.sha256(_norm(res.get("out")).encode()).hexdigest(),
                           "err_excerpt": _norm(res.get("err"))[:200]}
                    records.append(rec)
                    ev.write(json.dumps(rec, ensure_ascii=False) + "\n")
    elapsed = time.perf_counter() - t0
    total = len(records)
    passed = sum(r["passed"] for r in records)
    fs = sum(r["false_success"] for r in records)
    lat = sorted(r["ms"] for r in records)
    p50 = lat[len(lat) // 2] if lat else 0
    p95 = lat[min(len(lat) - 1, int(len(lat) * .95))] if lat else 0
    report = {
        "ok": True, "kind": "synthetic-scale", "independent": False,
        "tasks": len(all_tasks), "nodes": [n.name for n in nodes], "runs": args.runs,
        "records": total, "passed": passed, "false_success": fs,
        "pass_rate": round(passed / total, 6), "false_success_rate": round(fs / total, 6),
        "latency_ms": {"p50": p50, "p95": p95}, "elapsed_s": round(elapsed, 2),
        "evidence_sha256": hashlib.sha256(
            "\n".join(json.dumps(r, sort_keys=True) for r in records).encode()).hexdigest(),
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "note": "Synthetic scale/regression test on one host; not external validation.",
    }
    with open(os.path.join(outdir, "report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    with open(os.path.join(outdir, "REPORT.md"), "w", encoding="utf-8") as f:
        f.write("# CrossNode-Bench — 1,000-task scale test\n\n")
        f.write("**Synthetic/regression, not independent fleet validation.**\n\n")
        f.write(f"- tasks: **{len(all_tasks)}** × nodes: **{len(nodes)}** × runs: **{args.runs}**\n")
        f.write(f"- records: **{total}**, passed: **{passed}/{total}** ({100*report['pass_rate']:.2f}%)\n")
        f.write(f"- false success: **{fs}** ({100*report['false_success_rate']:.2f}%)\n")
        f.write(f"- elapsed: **{elapsed:.2f}s**, p50 {p50} ms, p95 {p95} ms\n")
        f.write("\nFalse successes are intentional mock liars; they validate detection, not model safety.\n")
    print(json.dumps(report, indent=2))
    return 0 if passed == total - 3 and fs == 3 else 1


if __name__ == "__main__":
    raise SystemExit(main())
