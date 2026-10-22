#!/usr/bin/env python3
"""E2: lease-bound proof chain; tamper and replay must fail closed."""
from __future__ import annotations

import json
import os
import secrets
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
import sys
sys.path.insert(0, str(HERE))
from lease_proof import Verifier, make_bundle  # noqa: E402

KEY = b"lab-key-not-for-production-000000"


def base(i: int, now: float) -> tuple[dict, dict, dict]:
    lease = {
        "lease_id": "L%03d" % i, "genome_hash": "g%03d" % i,
        "cmd_sha": "c%03d" % i, "nonce": secrets.token_hex(8),
        "audience": "protean/vastvm", "exp": now + 60,
    }
    report = {
        "lease_id": lease["lease_id"], "genome_hash": lease["genome_hash"],
        "cmd_sha": lease["cmd_sha"], "out_sha": "o%03d" % i,
        "status": "confirmed",
    }
    evidence = {"out_sha": report["out_sha"], "cmd_sha": report["cmd_sha"]}
    return lease, report, evidence


def main() -> int:
    now = time.time()
    bundle = make_bundle(*base(1, now), KEY)
    good = Verifier(KEY).verify(bundle, now)
    cases = []

    for name, mutate in [
        ("report_observed", lambda b: b["report"].__setitem__("out_sha", "evil")),
        ("lease_id", lambda b: b["lease"].__setitem__("lease_id", "L999")),
        ("genome", lambda b: b["lease"].__setitem__("genome_hash", "evil")),
        ("cmd", lambda b: b["report"].__setitem__("cmd_sha", "evil")),
        ("evidence", lambda b: b["evidence"].__setitem__("out_sha", "evil")),
        ("status", lambda b: b["report"].__setitem__("status", "done")),
        ("audience", lambda b: b["lease"].__setitem__("audience", "other")),
        ("expired", lambda b: b["lease"].__setitem__("exp", now - 1)),
    ]:
        bad = json.loads(json.dumps(bundle))
        mutate(bad)
        cases.append((name, Verifier(KEY).verify(bad, now)))

    replay_v = Verifier(KEY)
    first = replay_v.verify(bundle, now)
    replay = replay_v.verify(bundle, now)

    false_confirm = sum(1 for _, r in cases if r["ok"]) + int(replay["ok"])
    result = {
        "true_claim": good,
        "replay_first": first,
        "replay_second": replay,
        "tamper_cases": [{"case": n, "ok": r["ok"], "reasons": r["reasons"]} for n, r in cases],
        "false_confirmed": false_confirm,
        "pass": good["ok"] and first["ok"] and not replay["ok"] and false_confirm == 0,
    }
    (HERE / "corpus" / "e2_results.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "tamper_cases"}, indent=2))
    print(json.dumps(result["tamper_cases"], indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
