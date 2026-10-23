#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys

from .cbr import Proposal, evaluate
from .client import GuardClient
from .plan import Lease, check
from .text import Cascade


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="gamai-guard")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan"); p.add_argument("json")
    p.add_argument("--lease", default='{"effects":{"fs.read":["/in"],"fs.write":["/out"]}}')
    t = sub.add_parser("text"); t.add_argument("text")
    t.add_argument("--embed", default=None)
    t.add_argument("--worker", default=None)
    w = sub.add_parser("worker")
    w.add_argument("action", choices=["health", "stats", "check", "check_many"])
    w.add_argument("--url", default="http://127.0.0.1:18091")
    w.add_argument("--text", action="append", default=[])
    c = sub.add_parser("cbr"); c.add_argument("intent"); c.add_argument("goal")
    c.add_argument("--evidence", action="append", default=[])
    c.add_argument("--proposer", default="agent"); c.add_argument("--approver", default="")
    c.add_argument("--ok", type=int, default=5); c.add_argument("--fail", type=int, default=0)
    a = ap.parse_args(argv)
    if a.cmd == "plan":
        plan = json.loads(a.json)
        print(json.dumps(check(plan, Lease.from_dict(json.loads(a.lease))), indent=2))
    elif a.cmd == "text":
        if a.worker:
            print(json.dumps(GuardClient(a.worker).check(a.text), indent=2))
        else:
            print(json.dumps(Cascade(a.embed).check(a.text), indent=2))
    elif a.cmd == "worker":
        gc = GuardClient(a.url)
        if a.action == "health":
            out = gc.health()
        elif a.action == "stats":
            out = gc.stats()
        elif a.action == "check":
            out = gc.check(a.text[0]) if a.text else {"error": "--text required"}
        else:
            out = {"results": gc.check_many(a.text)}
        print(json.dumps(out, indent=2))
    else:
        p = Proposal(a.intent, a.goal, a.evidence, a.proposer, a.approver, a.ok, a.fail)
        print(json.dumps(evaluate(p), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
