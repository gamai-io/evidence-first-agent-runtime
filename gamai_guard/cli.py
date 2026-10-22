#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys

from .cbr import Proposal, evaluate
from .plan import Lease, check
from .text import Cascade


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="gamai-guard")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan"); p.add_argument("json")
    p.add_argument("--lease", default='{"effects":{"fs.read":["/in"],"fs.write":["/out"]}}')
    t = sub.add_parser("text"); t.add_argument("text")
    t.add_argument("--embed", default=None)
    c = sub.add_parser("cbr"); c.add_argument("intent"); c.add_argument("goal")
    c.add_argument("--evidence", action="append", default=[])
    c.add_argument("--proposer", default="agent"); c.add_argument("--approver", default="")
    c.add_argument("--ok", type=int, default=5); c.add_argument("--fail", type=int, default=0)
    a = ap.parse_args(argv)
    if a.cmd == "plan":
        plan = json.loads(a.json)
        print(json.dumps(check(plan, Lease.from_dict(json.loads(a.lease))), indent=2))
    elif a.cmd == "text":
        print(json.dumps(Cascade(a.embed).check(a.text), indent=2))
    else:
        p = Proposal(a.intent, a.goal, a.evidence, a.proposer, a.approver, a.ok, a.fail)
        print(json.dumps(evaluate(p), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
