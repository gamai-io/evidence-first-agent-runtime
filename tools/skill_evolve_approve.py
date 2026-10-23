#!/usr/bin/env python3
"""Sign one exact skill-evolve candidate (name + sha) for review-only apply."""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import time

KEY = "/opt/gama-harness/.skill_evolve_approval_key"
APPROVALS = "/opt/gama-harness/_skill_evolve_approvals.json"


def canon(name, sha, proposer, approver, ts) -> str:
    return json.dumps({"name": name, "sha": sha, "proposer": proposer,
                       "approver": approver, "ts": ts},
                      sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--sha", required=True)
    ap.add_argument("--proposer", default="agent")
    ap.add_argument("--approver", required=True)
    a = ap.parse_args()
    if a.proposer == a.approver:
        raise SystemExit("proposer and approver must differ")
    if len(a.sha) != 64:
        raise SystemExit("sha must be 64 hex chars")
    os.makedirs(os.path.dirname(KEY), exist_ok=True)
    if not os.path.exists(KEY):
        with open(KEY, "wb") as f:
            f.write(os.urandom(32))
        os.chmod(KEY, 0o600)
    key = open(KEY, "rb").read()
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    sig = hmac.new(key, canon(a.name, a.sha, a.proposer, a.approver, ts).encode(),
                   hashlib.sha256).hexdigest()
    try:
        data = json.loads(open(APPROVALS, encoding="utf-8").read())
    except Exception:
        data = {}
    data[a.name] = {"sha": a.sha, "proposer": a.proposer, "approver": a.approver,
                    "ts": ts, "sig": sig}
    with open(APPROVALS, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.chmod(APPROVALS, 0o600)
    print("approved %s sha=%s" % (a.name, a.sha[:12]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
