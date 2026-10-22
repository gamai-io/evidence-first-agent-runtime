#!/usr/bin/env python3
"""Dependency-free tests for crossnode-bench."""
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import crossnode as cn  # noqa: E402

CASES = []


def test(fn):
    CASES.append(fn)
    return fn


@test
def judge_true_pass():
    r = cn.judge(cn.TASKS[2], {"ok": True, "rc": 0, "out": "42", "err": ""})
    assert r["passed"] and not r["false_success"]


@test
def judge_false_success():
    r = cn.judge(cn.TASKS[2], {"ok": True, "rc": 0, "out": "41", "err": ""})
    assert r["false_success"] and not r["passed"]


@test
def judge_honest_failure():
    r = cn.judge(cn.TASKS[2], {"ok": False, "rc": 1, "out": "", "err": "boom"})
    assert not r["passed"] and not r["false_success"]


@test
def probe_honest_failure_passes():
    task = [t for t in cn.TASKS if t.id == "P1"][0]
    r = cn.judge(task, {"ok": False, "rc": 1, "out": "", "err": "not found"})
    assert r["passed"] and not r["false_success"]


@test
def probe_liar_is_false_success():
    task = [t for t in cn.TASKS if t.id == "P1"][0]
    r = cn.judge(task, {"ok": True, "rc": 0, "out": "", "err": "timed out"})
    assert r["false_success"] and not r["passed"]


@test
def demo_detects_lying_nodes():
    out = tempfile.mkdtemp(prefix="cnb-")
    report = cn.run_suite(cn.demo_nodes(), runs=1, outdir=out)
    assert report["false_success"] == 2, report["false_success"]
    assert report["passed"] == 46, report["passed"]
    assert report["records"] == 48
    assert len(report["evidence_sha256"]) == 64


@test
def report_files_written():
    out = tempfile.mkdtemp(prefix="cnb-")
    cn.run_suite([cn.LocalNode("node-a")], runs=1, outdir=out)
    for name in ("evidence.jsonl", "report.json", "REPORT.md"):
        assert os.path.exists(os.path.join(out, name)), name
    report = json.load(open(os.path.join(out, "report.json")))
    assert report["ok"] is True


@test
def evidence_lines_match_records():
    out = tempfile.mkdtemp(prefix="cnb-")
    report = cn.run_suite([cn.LocalNode("node-a")], runs=1, outdir=out)
    lines = [l for l in open(os.path.join(out, "evidence.jsonl")) if l.strip()]
    assert len(lines) == report["records"]


@test
def probe_filtering():
    honest = cn.LocalNode("node-a")
    liar = cn.MockLiar("node-b", cn.LocalNode("b-inner"), probe="nonexistent-program")
    out = tempfile.mkdtemp(prefix="cnb-")
    report = cn.run_suite([honest, liar], runs=1, outdir=out)
    assert report["records"] == 32  # 16 tasks x 2 nodes
    assert report["false_success"] == 1


@test
def latency_present():
    out = tempfile.mkdtemp(prefix="cnb-")
    report = cn.run_suite([cn.LocalNode("node-a")], runs=1, outdir=out)
    assert report["latency_ms"]["p50"] >= 0


def main():
    failed = 0
    for fn in CASES:
        try:
            fn()
            print("PASS", fn.__name__)
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print("FAIL", fn.__name__, "->", exc)
    print("\n%d/%d passed" % (len(CASES) - failed, len(CASES)))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
