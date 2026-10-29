#!/usr/bin/env python3
"""1,000 tasks across 5 real nodes including Windows.

Per node: 100 arithmetic, 50 echo, 40 file write/read, 10 failure probes.
Linux uses python3/sha; Windows uses PowerShell. Commands are non-destructive.
"""
from __future__ import annotations

import argparse, concurrent.futures as cf, hashlib, json, os, time
from dataclasses import dataclass
from crossnode import CliNode, _norm

OS = {"oracle": "linux", "linux3": "linux", "vast": "linux",
      "kuca": "windows", "podrum": "windows"}


@dataclass
class T:
    id: str
    kind: str
    cmd: str
    expected: str
    probe: bool = False


def build(node: str, count: int = 200) -> list[T]:
    osname = OS[node]
    out: list[T] = []
    for i in range(100):
        a, b = i * 17 + 3, i % 23 + 2
        val = a * b + i
        if osname == "linux":
            cmd = f'python3 -c "print({a}*{b}+{i})"'
        else:
            cmd = f'powershell -NoProfile -Command "Write-Output ({a}*{b}+{i})"'
        out.append(T(f"M{node[:2]}{i:03d}", "calc", cmd, str(val)))
    for i in range(50):
        tok = f"ECHO-{node}-{i:03d}"
        out.append(T(f"E{node[:2]}{i:03d}", "echo", f"echo {tok}", tok))
    for i in range(40):
        tok = f"FILE-{node}-{i:03d}"
        if osname == "linux":
            path = f"/tmp/gama_five_{node}_{i:03d}"
            cmd = f"printf {tok} >{path} && cat {path}"
        else:
            path = rf"C:\Users\Public\gama_five_{node}_{i:03d}"
            cmd = (f'powershell -NoProfile -Command "Set-Content -Path {path} -Value {tok}; '
                   f'Get-Content {path}"')
        out.append(T(f"F{node[:2]}{i:03d}", "file", cmd, tok))
    for i in range(10):
        out.append(T(f"P{node[:2]}{i:03d}", "probe", f"run missing-five-{node}-{i:03d}", "", True))
    assert len(out) == count
    return out


def judge(t: T, r: dict) -> dict:
    claim = bool(r.get("ok")); out = _norm(r.get("out"))
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
    ap.add_argument("--nodes", default="oracle,linux3,vast,kuca,podrum")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    nodes = [x.strip() for x in a.nodes.split(",") if x.strip()]
    by = {n: build(n) for n in nodes}
    outdir = a.out or os.path.join(os.path.dirname(os.path.abspath(__file__)), "runs", "five-" + time.strftime("%Y%m%d-%H%M%S"))
    os.makedirs(outdir, exist_ok=True)
    adapters = {n: CliNode(n, n) for n in nodes}

    def work(n: str) -> list[dict]:
        recs = []
        for t in by[n]:
            r = adapters[n].run(t.cmd, timeout=35)
            for k in range(5):
                e = str(r.get("err") or "")
                if "busy (lease)" not in e and "Connection refused" not in e:
                    break
                time.sleep(0.4 * (k + 1))
                r = adapters[n].run(t.cmd, timeout=35)
            v = judge(t, r)
            recs.append({"run": 1, "node": n, "task": t.id, "kind": t.kind,
                         "cmd_sha256": hashlib.sha256(t.cmd.encode()).hexdigest()[:16],
                         "ms": r.get("ms", 0), "rc": r.get("rc"),
                         "claim_ok": v["claim_ok"], "truth_ok": v["truth_ok"],
                         "passed": v["passed"], "false_success": v["false_success"],
                         "why": v["why"],
                         "out_sha256": hashlib.sha256(_norm(r.get("out")).encode()).hexdigest(),
                         "err_excerpt": _norm(r.get("err"))[:200]})
        return recs

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
    rep = {"ok": True, "kind": "five-node-mixed", "independent": True, "nodes": nodes,
           "tasks": total, "records": total, "passed": passed, "false_success": fs,
           "pass_rate": round(passed/total, 6), "false_success_rate": round(fs/total, 6),
           "latency_ms": {"p50": lat[len(lat)//2], "p95": lat[min(len(lat)-1, int(len(lat)*.95))]},
           "elapsed_s": round(elapsed, 2), "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "evidence_sha256": hashlib.sha256("\n".join(json.dumps(r, sort_keys=True) for r in records).encode()).hexdigest()}
    json.dump(rep, open(os.path.join(outdir, "report.json"), "w"), indent=2)
    with open(os.path.join(outdir, "REPORT.md"), "w") as f:
        f.write("# Five-node mixed 1,000-task run\n\n")
        f.write(f"- nodes: {', '.join(nodes)}\n- tasks: **{total}**\n- passed: **{passed}/{total}**\n")
        f.write(f"- false success: **{fs}**\n- elapsed: **{elapsed:.2f}s**\n")
        f.write(f"- p50/p95: {rep['latency_ms']['p50']} / {rep['latency_ms']['p95']} ms\n")
        for r in records:
            if not r["passed"]: f.write(f"- FAIL `{r['node']}` `{r['task']}`: {r['why']} `{r['err_excerpt']}`\n")
    print(json.dumps(rep, indent=2))
    return 0 if fs == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
