#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verifikacija LUMI bench JSONL-a: schema, reconciliation, percentili, false-success.

  python3 check_results.py --jsonl run1.jsonl --expect-n 1000 --strict
  python3 check_results.py --jsonl run1.jsonl --md table.md

Pravila:
  - 1 red = 1 pokusaj; finalni redovi su svi (retry je vec u ms; nema skrivenih redova)
  - ok=true zahtijeva status=200 i text_len>0 (prazan 200 je false-green)
  - false_success=true je FAIL cak i ako je ok=true
  - duplikat (run_id,i) je FAIL
  - strict: exit 1 ako bilo koji FAIL
"""
import argparse, json, statistics, sys
from collections import defaultdict

REQ = ["run_id", "i", "case", "mode", "ok", "status", "ms", "false_success"]


def pct(a, p):
    if not a:
        return None
    a = sorted(a)
    k = max(0, min(len(a) - 1, int(round((p / 100.0) * (len(a) - 1)))))
    return a[k]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jsonl", required=True)
    ap.add_argument("--expect-n", type=int, default=0)
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--md", default="")
    ap.add_argument("--json-out", default="")
    a = ap.parse_args()

    rows, bad = [], []
    for ln, line in enumerate(open(a.jsonl, encoding="utf-8", errors="replace"), 1):
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except Exception as e:
            bad.append({"line": ln, "err": "json", "detail": str(e)[:120]})
            continue
        miss = [k for k in REQ if k not in d]
        if miss:
            bad.append({"line": ln, "err": "schema", "detail": "missing %s" % ",".join(miss)})
            continue
        rows.append(d)

    dups = defaultdict(int)
    for r in rows:
        dups[(r["run_id"], r["i"])] += 1
    dup = [{"run_id": k[0], "i": k[1], "n": v} for k, v in dups.items() if v > 1]

    ok = [r for r in rows if r["ok"]]
    err = [r for r in rows if not r["ok"]]
    empty_ok = [r for r in ok if int(r.get("text_len") or 0) == 0]
    fs = [r for r in ok if r["false_success"] is True]
    checked = [r for r in ok if r["false_success"] is not None]
    bad_status = [r for r in rows if r["ok"] and int(r["status"]) != 200]

    lat = [r["ms"] for r in ok]
    tt = [r["ttft_ms"] for r in ok if r.get("ttft_ms") is not None]

    by_case = defaultdict(lambda: {"n": 0, "ok": 0, "fs": 0, "ms": [], "ttft": []})
    for r in rows:
        b = by_case[r["case"]]
        b["n"] += 1
        if r["ok"]:
            b["ok"] += 1
            b["ms"].append(r["ms"])
            if r.get("ttft_ms") is not None:
                b["ttft"].append(r["ttft_ms"])
            if r["false_success"] is True:
                b["fs"] += 1

    fails = []
    if bad:
        fails.append("schema/json: %d" % len(bad))
    if dup:
        fails.append("duplicate (run_id,i): %d" % len(dup))
    if empty_ok:
        fails.append("ok but empty text: %d" % len(empty_ok))
    if bad_status:
        fails.append("ok but status!=200: %d" % len(bad_status))
    if a.expect_n and len(rows) != a.expect_n:
        fails.append("count %d != expect %d" % (len(rows), a.expect_n))
    if fs:
        fails.append("false_success: %d" % len(fs))

    summary = {
        "file": a.jsonl, "rows": len(rows), "ok": len(ok), "err": len(err),
        "false_success": len(fs), "false_checked": len(checked),
        "false_success_rate": round(len(fs) / len(checked), 4) if checked else None,
        "ms_p50": pct(lat, 50), "ms_p95": pct(lat, 95), "ms_p99": pct(lat, 99),
        "ttft_p50": pct(tt, 50), "ttft_p95": pct(tt, 95), "ttft_p99": pct(tt, 99),
        "duplicates": len(dup), "schema_bad": len(bad), "empty_ok": len(empty_ok),
        "fails": fails, "verdict": "PASS" if not fails else "FAIL",
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    if a.md:
        lines = ["| case | n | ok | false_success | p50 ms | ttft p50 |",
                 "|---|---:|---:|---:|---:|---:|"]
        for c in sorted(by_case):
            b = by_case[c]
            lines.append("| %s | %d | %d | %d | %s | %s |" % (
                c, b["n"], b["ok"], b["fs"],
                round(statistics.median(b["ms"]), 1) if b["ms"] else "-",
                round(statistics.median(b["ttft"]), 1) if b["ttft"] else "-"))
        open(a.md, "w", encoding="utf-8").write("\n".join(lines) + "\n")
        print("md:", a.md)

    if a.json_out:
        json.dump(summary, open(a.json_out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print("json:", a.json_out)

    if a.strict and fails:
        sys.exit(1)


if __name__ == "__main__":
    main()
