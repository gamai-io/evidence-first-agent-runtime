#!/usr/bin/env python3
"""Verify an exported LUMI benchmark JSONL: schema, duplicates, false-success, SHA-256.

Usage:
  python3 lumi/verify_raw.py guard_10000_23453363.jsonl [--expect-n 10000] [--sha256 HEX] [--strict]
Exit 1 on failure in --strict mode.
"""
import argparse, hashlib, json, sys

REQ = ("prompt_sha", "status", "ms", "text")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("jsonl")
    ap.add_argument("--expect-n", type=int, default=0)
    ap.add_argument("--sha256", default="")
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()
    h = hashlib.sha256()
    rows, bad, dup, fs, fs_checked = 0, [], set(), 0, 0
    with open(a.jsonl, "rb") as f:
        for raw in f:
            h.update(raw)
            if not raw.strip():
                continue
            rows += 1
            try:
                r = json.loads(raw)
            except Exception as e:
                bad.append(f"json:{e}")
                continue
            missing = [k for k in REQ if k not in r]
            if missing:
                bad.append(f"missing:{,.join(missing)}")
            ps = r.get("prompt_sha")
            if ps is not None:
                if ps in dup:
                    bad.append("duplicate_prompt_sha")
                dup.add(ps)
            v = r.get("false_success")
            if v is not None:
                fs_checked += 1
                if v:
                    fs += 1
    digest = h.hexdigest()
    out = {"file": a.jsonl, "rows": rows, "sha256": digest, "schema_bad": len(bad),
           "duplicates": len(dup) and 0, "false_success": fs, "false_checked": fs_checked,
           "false_success_rate": (fs / fs_checked) if fs_checked else None,
           "problems": bad[:20]}
    print(json.dumps(out, indent=2))
    fail = bool(bad) or (a.expect_n and rows != a.expect_n) or (a.sha256 and digest != a.sha256)
    return 1 if (a.strict and fail) else 0

if __name__ == "__main__":
    sys.exit(main())
