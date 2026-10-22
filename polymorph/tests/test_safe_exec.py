#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
SAFE = HERE / "safe_exec.py"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(path: Path, digest: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SAFE), str(path), digest],
                          capture_output=True, text=True, timeout=10)


def main() -> int:
    d = Path(tempfile.mkdtemp(prefix="safe-exec-"))
    script = d / "ok.sh"
    script.write_text("#!/bin/sh\necho SAFE\n", encoding="utf-8")
    digest = sha(script)
    assert run(script, digest).stdout.strip() == "SAFE"

    link = d / "link.sh"
    link.symlink_to(script)
    r = run(link, digest)
    assert r.returncode == 126 and "open_no_follow_denied" in r.stdout

    r = run(script, "0" * 64)
    assert r.returncode == 126 and "pre_exec_hash_mismatch" in r.stdout
    print("3/3 passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
