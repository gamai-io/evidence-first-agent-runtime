from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAFE = ROOT / "polymorph" / "safe_exec.py"


def run_pinned(path: str, expected: str, args: list[str] | None = None,
               timeout: int = 10) -> dict:
    receipt = tempfile.mktemp(prefix="guard-receipt-", suffix=".json")
    cmd = [sys.executable, str(SAFE), "--receipt", receipt, path, expected]
    cmd += list(args or [])
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"ok": False, "denied": "timeout", "out": "", "rc": None,
                "admitted_sha": expected, "executed_sha": None}
    try:
        rec = json.load(open(receipt, encoding="utf-8"))
    except Exception:
        rec = {}
    ok = p.returncode == 0 and rec.get("ok") and rec.get("executed_sha") == expected
    return {
        "ok": bool(ok), "out": p.stdout.strip(), "err": p.stderr.strip(),
        "rc": p.returncode, "admitted_sha": expected,
        "executed_sha": rec.get("executed_sha"),
        "receipt": rec,
    }
