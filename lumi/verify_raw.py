#!/usr/bin/env python3
"""Verify an exported LUMI benchmark JSONL: schema, duplicates, false-success, SHA-256."""
import argparse, hashlib, json, sys

REQ = ("prompt_sha", "status", "ms", "text")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jsonl")
    ap.add_argument("--expect-n", type=int, default=0)
    ap.add_argument("--sha256", default="")
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()
    h = hashlib.sha256(); rows = 0; bad = []; seen = set(); fs = 0; checked = 0; dup_rows = 0
    with open(a.jsonl, "rb") as f:
        for raw in f:
            h.update(raw)
            if not raw.strip():
                continue
            rows += 1
            try:
                r = json.loads(raw)
            except Exception as e:
                bad.append("json:" + str(e)); continue
            miss = [k for k in REQ if k not in r]
            if miss:
                bad.append("missing:" + ",".join(miss))
            ps = r.get("prompt_sha")
            if ps is not None:
                if ps in seen:
                    dup_rows += 1
                else:
                    seen.add(ps)
            v = r.get("false_success")
            if v is not None:
                checked += 1
                if v:
                    fs += 1
    digest = h.hexdigest()
    out = {"file": a.jsonl, "rows": rows, "sha256": digest, "schema_bad": len(bad),
           "distinct_prompt_sha": len(seen), "duplicate_rows": dup_rows,
           "false_success": fs, "false_checked": checked,
           "false_success_rate": (fs / checked) if checked else None,
           "problems": bad[:20]}
    print(json.dumps(out, indent=2))
    fail = bool(bad) or (a.expect_n and rows != a.expect_n) or (a.sha256 and digest != a.sha256)
    return 1 if (a.strict and fail) else 0

if __name__ == "__main__":
    sys.exit(main())
