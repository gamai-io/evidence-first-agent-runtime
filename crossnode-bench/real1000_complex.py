#!/usr/bin/env python3
"""1,000 real Linux tasks across the fleet: arithmetic, file IO, hashes, probes."""
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
    n = 1000
    out: list[tuple[str, T]] = []
    for i in range(n):
        node = nodes[i % len(nodes)]
        if i < 400:
            a, b = i * 17 + 3, i % 23 + 2
            out.append((node, T(f"M{i:04d}", "calc", f'python3 -c "print({a}*{b}+{i})"', str(a * b + i))))
        elif i < 700:
            token = f"FILE-{i:04d}"
            out.append((node, T(f"F{i:04d}", "file", f"printf {token} >/tmp/gama_bench_{i:04d} && cat /tmp/gama_bench_{i:04d}", token)))
        elif i < 900:
            token = f"HASH-{i:04d}"
            exp = hashlib.sha256(token.encode()).hexdigest()
            out.append((node, T(f"H{i:04d}", "hash", f"printf {token} | sha256sum | cut -d' ' -f1", exp)))
        else:
            out.append((node, T(f"P{i:04d}", "probe", f"run missing-complex-{i:04d}", "", True)))
    return out


def judge(t: T, res: dict) -> dict:
    claim = bool(res.get("ok")); out = _norm(res.get("out"))
    if t.probe:
        truth = not claim
        return {"claim_ok": claim, "truth_ok": truth, "passed": truth,
                "false_success": claim, "why": "probe must fail" if claim else "probe honestly failed"}
    truth = out == t.expected
    return {"claim_ok": claim, "truth_ok": truth, "passed": claim and truth,
            "false_success": claim and not truth,
            "why": "expected stdout" if claim and truth else ("claim without stdout" if claim else "failed")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nodes", default="oracle,linux3,vast")
    ap.add_argument("--per-node", type=int, default=250)
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    nodes = [x.strip() for x in a.nodes.split(",") if x.strip()]
    jobs = build(nodes, a.per_node)
    by = {n: [] for n in nodes}
    for n, t in jobs: by[n].append(t)
    outdir = a.out or os.path.join(os.path.dirname(os.path.abspath(__file__)), "runs", "real1000c-" + time.strftime("%Y%m%d-%H%M%S"))
    os.makedirs(outdir, exist_ok=True)
    nodes_ad = {n: CliNode(n, n) for n in nodes}

    def work(n):
        out = []
        for t in by[n]:
            r = nodes_ad[n].run(t.cmd, timeout=30)
            for _try in range(4):
                _e = str(r.get("err") or "")
                if "busy (lease)" not in _e and "Connection refused" not in _e:
                    break
                time.sleep(0.4 * (_try + 1))
                r = nodes_ad[n].run(t.cmd, timeout=30)
            v = judge(t, r)
            out.append({"run": 1, "node": n, "task": t.id, "kind": t.kind,
                        "cmd_sha256": hashlib.sha256(t.cmd.encode()).hexdigest()[:16],
                        "ms": r.get("ms", 0), "rc": r.get("rc"),
                        "claim_ok": v["claim_ok"], "truth_ok": v["truth_ok"],
                        "passed": v["passed"], "false_success": v["false_success"],
                        "why": v["why"],
                        "out_sha256": hashlib.sha256(_norm(r.get("out")).encode()).hexdigest(),
                        "err_excerpt": _norm(r.get("err"))[:200]})
        return out
    t0 = time.perf_counter()
    records = []
    with cf.ThreadPoolExecutor(max_workers=len(nodes)) as ex:
        for recs in ex.map(work, nodes): records.extend(recs)
    elapsed = time.perf_counter() - t0
    records.sort(key=lambda x: (x["node"], x["task"]))
    with open(os.path.join(outdir, "evidence.jsonl"), "w") as f:
        for r in records: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    total = len(records); passed = sum(r["passed"] for r in records); fs = sum(r["false_success"] for r in records)
    lat = sorted(r["ms"] for r in records)
    report = {"ok": True, "kind": "real-fleet-complex", "independent": True, "nodes": nodes,
              "tasks": total, "records": total, "passed": passed, "false_success": fs,
              "pass_rate": round(passed/total, 6), "false_success_rate": round(fs/total, 6),
              "latency_ms": {"p50": lat[len(lat)//2], "p95": lat[min(len(lat)-1, int(len(lat)*.95))]},
              "elapsed_s": round(elapsed, 2), "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "evidence_sha256": hashlib.sha256("\n".join(json.dumps(r, sort_keys=True) for r in records).encode()).hexdigest()}
    json.dump(report, open(os.path.join(outdir, "report.json"), "w"), indent=2)
    with open(os.path.join(outdir, "REPORT.md"), "w") as f:
        f.write("# Real complex 1,000-task run\n\n")
        f.write(f"- nodes: {', '.join(nodes)}\n- tasks: **{total}**\n- passed: **{passed}/{total}**\n")
        f.write(f"- false success: **{fs}**\n- elapsed: **{elapsed:.2f}s**\n")
        f.write(f"- p50/p95: {report['latency_ms']['p50']} / {report['latency_ms']['p95']} ms\n")
        for r in records:
            if not r["passed"]: f.write(f"- FAIL `{r['node']}` `{r['task']}`: {r['why']} `{r['err_excerpt']}`\n")
    print(json.dumps(report, indent=2))
    return 0 if fs == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
