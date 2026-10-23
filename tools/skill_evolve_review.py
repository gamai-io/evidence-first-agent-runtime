#!/usr/bin/env python3
"""Review-only wrapper for gama_skill_evolve.

Builds candidates from cases.db, runs the static/synthetic gate, and appends a
review record. It NEVER deploys. Deployment requires a signed approval and
`--apply-approved`.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import sys
import time

sys.path.insert(0, "/root/gamaos")
import gama_cases as gc  # type: ignore
import gama_skill_evolve as EV  # type: ignore

REVIEW = "/opt/gama-harness/_skill_evolve_review.jsonl"
APPROVALS = "/opt/gama-harness/_skill_evolve_approvals.json"
KEY = "/opt/gama-harness/.skill_evolve_approval_key"


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def _canon(name, sha, proposer, approver, ts) -> str:
    return json.dumps({"name": name, "sha": sha, "proposer": proposer,
                       "approver": approver, "ts": ts},
                      sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _load_approvals() -> dict:
    try:
        return json.loads(open(APPROVALS, encoding="utf-8").read())
    except Exception:
        return {}


def _approved(name: str, sha: str) -> bool:
    a = _load_approvals().get(name)
    if not a or a.get("sha") != sha:
        return False
    if not a.get("proposer") or not a.get("approver") or a["proposer"] == a["approver"]:
        return False
    try:
        key = open(KEY, "rb").read()
    except Exception:
        return False
    want = hmac.new(key, _canon(name, sha, a["proposer"], a["approver"], a["ts"]).encode(),
                    hashlib.sha256).hexdigest()
    return hmac.compare_digest(want, a.get("sig", ""))


def build(min_ok: int):
    for p in gc.promote(min_ok)[: EV.MAX_RUN]:
        intent = p.get("intent", "")
        recs = gc.find(intent, k=1)
        goal = recs[0]["goal"] if recs else intent
        steps = recs[0]["steps"] if recs else []
        name = "gama-auto-" + EV._slug(intent)
        content = EV.build_skill_md(name, goal, intent, steps, p.get("ok", 0))
        g = EV.gate(name, content, steps)
        yield {"name": name, "intent": intent, "goal": goal, "ok": p.get("ok", 0),
               "sha": _sha(content), "gate_ok": g["ok"], "score": g.get("score"),
               "failed": [c["id"] for c in g.get("checks", []) if not c["ok"]],
               "content": content, "steps": steps}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min", type=int, default=5)
    ap.add_argument("--apply-approved", action="store_true")
    a = ap.parse_args()
    os.makedirs(os.path.dirname(REVIEW), exist_ok=True)
    seen = set()
    try:
        for line in open(REVIEW, encoding="utf-8"):
            r = json.loads(line)
            seen.add((r.get("name"), r.get("sha")))
    except Exception:
        pass
    proposed = deployed = 0
    for c in build(a.min):
        proposed += 1
        rec = {k: c[k] for k in ("name", "intent", "goal", "ok", "sha", "gate_ok", "score", "failed")}
        rec["ts"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        if (c["name"], c["sha"]) not in seen:
            with open(REVIEW, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print("[review] %-55s gate=%s sha=%s" % (c["name"], "OK" if c["gate_ok"] else "REJECT", c["sha"][:12]))
        if a.apply_approved and c["gate_ok"] and _approved(c["name"], c["sha"]):
            os.makedirs(os.path.join(EV.CAND, c["name"]), exist_ok=True)
            res = EV.deploy(c["name"], c["content"],
                            meta={"goal": c["goal"], "intent": c["intent"], "mode": "approved"}, steps=c["steps"])
            print("  -> deploy", res.get("status"))
            deployed += 1 if res.get("ok") else 0
    print("reviewed=%d deployed=%d review_file=%s" % (proposed, deployed, REVIEW))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
