from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "polymorph"))
from lease_proof import Verifier, make_bundle, sign  # noqa: E402
from .executed import run_pinned  # noqa: E402


def execution_bundle(lease: dict, report: dict, evidence: dict, key: bytes,
                     path: str, expected: str, args: list[str] | None = None) -> dict:
    run = run_pinned(path, expected, args)
    report = dict(report)
    report["out_sha"] = run.get("executed_sha") or ""
    report["executed_sha"] = run.get("executed_sha")
    evidence = dict(evidence)
    evidence["out_sha"] = report["out_sha"]
    evidence["run"] = run
    return make_bundle(lease, report, evidence, key)


__all__ = ["execution_bundle", "Verifier", "make_bundle", "sign"]
