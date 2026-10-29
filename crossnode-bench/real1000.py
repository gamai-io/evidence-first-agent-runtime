#!/usr/bin/env python3
"""Run 1,000 distinct tasks across real fleet nodes.

Tasks are assigned round-robin; every node executes only its share. This is a
real execution test, not a simulated fleet. Commands are limited to `echo` and
`run <missing>` probes, so the test is non-destructive.

  python3 real1000.py
  python3 real1000.py --nodes oracle,linux3,vast,kuca,podrum --per-node 200
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import json
import os
import time
from dataclasses import dataclass

from crossnode import CliNode, _norm


@dataclass
class T:
    id: str
    kind: str
    cmd: str
    expected: str
    probe: bool = False


def build(nodes: list[str], per_node: int) -> list[tuple[str, T]]:
    out: list[tuple[str, T]] = []
    total = len(nodes) * per_node
    probe_n = max(1, total // 20)  # 5%
    for i in range(total):
        node = nodes[i % len(nodes)]
        if i < probe_n:
            t = T(f"P{i:04d}", "probe", f"run missing-real1000-{i:04d}", "", True)
        else:
            token = f"REAL-{i:04d}"
            t = T(f"E{i:04d}", "read", f"echo {token}", token)
        out.append((node, t))
    return out


def judge(t: T, res: dict) -> dict:
    claim = bool(res.get("ok"))
    out = _norm(res.get("out"))
    if t.probe:
        truth = not claim
        return {"claim_ok": claim, "truth_ok": truth, "passed": truth,
                "false_success": claim and truth is False,
                "why": "probe must fail" if claim else "probe honestly failed"}
    truth = out == t.expected
    return {"claim_ok": claim, "truth_ok": truth, "passed": claim and truth,
            "false_success": claim and not truth,
            "why": "expected stdout" if claim and truth else ("claim without expected stdout" if claim else "failed")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nodes", default="oracle,linux3,vast,kuca,podrum")
    ap.add_argument("--per-node", type=int, default=200)
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    nodes = [x.strip() for x in a.nodes.split(",") if x.strip()]
    jobs = build(nodes, a.per_node)
    ts = time.strftime("%Y%m%d-%H%M%S")
    outdir = a.out or os.path.join(os.path.dirname(os.path.abspath(__file__)), "runs", f"real1000-{ts}")
    os.makedirs(outdir, exist_ok=True)
    adapters = {n: CliNode(n, n) for n in nodes}
    by_node: dict[str, list[T]] = {n: [] for n in nodes}
    for n, t in jobs:
        by_node[n].append(t)

    def run_node(n: str) -> list[dict]:
        recs = []
        for t in by_node[n]:
            res = adapters[n].run(t.cmd, timeout=25)
            v = judge(t, res)
            recs.append({"run": 1, "node": n, "task": t.id, "kind": t.kind,
                         "cmd_sha256": hashlib.sha256(t.cmd.encode()).hexdigest()[:16],
                         "ms": res.get("ms", 0), "rc": res.get("rc"),
                         "claim_ok": v["claim_ok"], "truth_ok": v["truth_ok"],
                         "passed": v["passed"], "false_success": v["false_success"],
                         "why": v["why"],
                         "out_sha256": hashlib.sha256(_norm(res.get("out")).encode()).hexdigest(),
                         "err_excerpt": _norm(res.get("err"))[:200]})
        return recs

    t0 = time.perf_counter()
    records = []
    with cf.ThreadPoolExecutor(max_workers=len(nodes)) as ex:
        for recs in ex.map(run_node, nodes):
            records.extend(recs)
    elapsed = time.perf_counter() - t0
    records.sort(key=lambda r: (r["node"], r["task"]))
    with open(os.path.join(outdir, "evidence.jsonl"), "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    total = len(records)
    passed = sum(r["passed"] for r in records)
    fs = sum(r["false_success"] for r in records)
    lat = sorted(r["ms"] for r in records)
    report = {"ok": True, "kind": "real-fleet", "independent": True,
              "nodes": nodes, "per_node": a.per_node, "tasks": total,
              "records": total, "passed": passed, "false_success": fs,
              "pass_rate": round(passed / total, 6) if total else 0,
              "false_success_rate": round(fs / total, 6) if total else 0,
              "latency_ms": {"p50": lat[len(lat)//2] if lat else 0,
                             "p95": lat[min(len(lat)-1, int(len(lat)*.95))] if lat else 0},
              "elapsed_s": round(elapsed, 2), "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "evidence_sha256": hashlib.sha256("\n".join(json.dumps(r, sort_keys=True) for r in records).encode()).hexdigest()}
    json.dump(report, open(os.path.join(outdir, "report.json"), "w"), indent=2)
    with open(os.path.join(outdir, "REPORT.md"), "w") as f:
        f.write("# Real fleet 1,000-task run\n\n")
        f.write(f"- nodes: {', '.join(nodes)}\n- tasks: **{total}** ({a.per_node}/node)\n")
        f.write(f"- passed: **{passed}/{total}** ({100*report['pass_rate']:.2f}%)\n")
        f.write(f"- false success: **{fs}**\n- elapsed: **{elapsed:.2f}s**\n")
        f.write(f"- p50/p95: {report['latency_ms']['p50']} / {report['latency_ms']['p95']} ms\n")
        for r in records:
            if not r["passed"]:
                f.write(f"- FAIL `{r['node']}` `{r['task']}`: {r['why']} `{r['err_excerpt']}`\n")
    print(json.dumps({k: report[k] for k in ("nodes","tasks","passed","false_success","pass_rate","latency_ms","elapsed_s","evidence_sha256")}, indent=2))
    return 0 if fs == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
