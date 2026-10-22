#!/usr/bin/env python3
"""Small CLI for the gamAI Trust Layer."""
from __future__ import annotations

import json
import sys

from . import check_injection, demo, verify_claims


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print("usage: gamai-trust demo | check <text> | verify <claims.json>")
        return 0 if argv else 2
    cmd = argv[0]
    if cmd == "demo":
        print(json.dumps(demo(), ensure_ascii=False, indent=2, default=str))
        return 0
    if cmd == "check":
        text = " ".join(argv[1:])
        print(json.dumps(check_injection(text), ensure_ascii=False, indent=2))
        return 0
    if cmd == "verify":
        if len(argv) < 2:
            print("usage: gamai-trust verify <claims.json>", file=sys.stderr)
            return 2
        with open(argv[1], "r", encoding="utf-8") as fh:
            data = json.load(fh)
        claims = data.get("claims") if isinstance(data, dict) else data
        report = verify_claims(claims or [],
                               data.get("evidence_sha256") if isinstance(data, dict) else None)
        print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
        return 0 if report.get("ok") else 1
    print("unknown command: %s" % cmd, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
