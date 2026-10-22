#!/usr/bin/env python3
"""Create a dual-control CBR approval.

The proposer is the agent; the reviewer must be a different principal and must
provide at least one effect-evidence token. The approval is HMAC-signed.
"""
from __future__ import annotations

import argparse
import os
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from gamai_guard.cbr import ApprovalStore, Proposal  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--intent", required=True)
    ap.add_argument("--goal", required=True)
    ap.add_argument("--evidence", action="append", required=True)
    ap.add_argument("--proposer", required=True)
    ap.add_argument("--reviewer", required=True)
    ap.add_argument("--ok", type=int, default=5)
    ap.add_argument("--fail", type=int, default=0)
    ap.add_argument("--store", default="/opt/gama-harness/_cbr_approvals.json")
    ap.add_argument("--key-file", default="/opt/gama-harness/.cbr_approval_key")
    args = ap.parse_args()
    kf = Path(args.key_file)
    if not kf.exists():
        kf.write_bytes(secrets.token_bytes(32))
        os.chmod(kf, 0o600)
    key = kf.read_bytes()
    p = Proposal(args.intent, args.goal, args.evidence, args.proposer, args.reviewer,
                 args.ok, args.fail)
    res = ApprovalStore(args.store, key).approve(p)
    print(res)
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
