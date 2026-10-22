#!/usr/bin/env python3
"""E1: mutation may not widen the capability envelope."""
from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from effect_lease import Lease, check  # noqa: E402

LEASE = Lease.from_dict({"effects": {
    "fs.read": ["/in"],
    "fs.write": ["/out"],
    "net.connect": ["api.internal"],
    "exec": ["/bin/true", "/bin/echo"],
    "db.read": ["/in/cache.db"],
    "send": ["mail", "chat"],
}})


def main() -> int:
    path = HERE / "corpus" / "e1.jsonl"
    if not path.exists():
        import gen_e1
        gen_e1.main()
    rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    out = []
    lat = []
    for row in rows:
        t0 = time.perf_counter()
        verdict = check(row, LEASE)
        lat.append((time.perf_counter() - t0) * 1000.0)
        out.append({**row, **verdict})
    benign = [r for r in out if r["kind"] == "benign"]
    malicious = [r for r in out if r["kind"] == "malicious"]
    allow_b = sum(1 for r in benign if r["allow"])
    deny_m = sum(1 for r in malicious if not r["allow"])
    cap_m = sum(1 for r in malicious if r["capability_gain"])
    result = {
        "plan": "E1 capability widening",
        "benign": len(benign),
        "malicious": len(malicious),
        "benign_allowed": allow_b,
        "malicious_denied": deny_m,
        "malicious_with_capability_gain": cap_m,
        "benign_false_deny": len(benign) - allow_b,
        "malicious_false_allow": len(malicious) - deny_m,
        "latency_p50_ms": round(statistics.median(lat), 4),
        "latency_p95_ms": round(sorted(lat)[int(len(lat) * 0.95)], 4),
        "pass": allow_b == len(benign) and deny_m == len(malicious) and cap_m == len(malicious),
        "results": out,
    }
    (HERE / "corpus" / "e1_results.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "results"}, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
