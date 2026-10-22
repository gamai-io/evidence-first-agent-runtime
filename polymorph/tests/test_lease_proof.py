#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from lease_proof import Verifier, make_bundle  # noqa: E402

KEY = b"test-key"
NOW = 1000.0


def base():
    lease = {"lease_id": "L1", "genome_hash": "g", "cmd_sha": "c",
             "nonce": "n1", "audience": "protean/vastvm", "exp": NOW + 10}
    report = {"lease_id": "L1", "genome_hash": "g", "cmd_sha": "c",
              "out_sha": "o", "status": "confirmed"}
    evidence = {"out_sha": "o"}
    return make_bundle(lease, report, evidence, KEY)


def main():
    v = Verifier(KEY)
    assert v.verify(base(), NOW)["ok"]
    # replay is consumed by the first successful verify
    assert not v.verify(base(), NOW)["ok"]

    b = base()
    b["report"]["out_sha"] = "evil"
    assert not Verifier(KEY).verify(b, NOW)["ok"]

    b = base()
    b["lease"]["exp"] = NOW - 1
    assert not Verifier(KEY).verify(b, NOW)["ok"]

    b = base()
    b["lease"]["audience"] = "other"
    assert not Verifier(KEY).verify(b, NOW)["ok"]

    print("5/5 passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
