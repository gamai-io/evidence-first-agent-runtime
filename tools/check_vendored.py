#!/usr/bin/env python3
"""Fail when a vendored component has drifted from its standalone repository.

This repository bundles copies of proofgate, gamai_trust, gamai_guard,
crossnode-bench and polymorph. Copies silently diverge; that is how the same
criteria ended up in three versions. This script compares the tracked files of
each vendored directory with the upstream repository at its default branch and
reports every file that differs, is missing or is extra.

Network is required (it clones shallow copies into a temp dir), so it runs on a
schedule and on demand, not on every push.

Exit codes: 0 no drift, 1 drift found, 2 the check itself could not run.
"""
from __future__ import annotations

import hashlib
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]

# vendored directory -> standalone repository
COMPONENTS = {
    "proofgate": "gamai-io/proofgate-runtime",
    "gamai_trust": "gamai-io/gamai-trust",
    "gamai_guard": "gamai-io/gamai-guard",
    "crossnode-bench": "gamai-io/crossnode-bench",
    "polymorph": "gamai-io/polymorph",
}

SKIP_NAMES = {".git", "__pycache__", ".pytest_cache", "node_modules"}
SKIP_SUFFIX = {".pyc", ".pyo"}


def tracked_files(base: pathlib.Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for path in base.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_NAMES for part in path.parts):
            continue
        if path.suffix in SKIP_SUFFIX:
            continue
        rel = path.relative_to(base).as_posix()
        out[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def main() -> int:
    drift = 0
    with tempfile.TemporaryDirectory() as td:
        for local, repo in COMPONENTS.items():
            here = ROOT / local
            if not here.is_dir():
                print(f"{local}: not vendored here, skipped")
                continue
            dest = pathlib.Path(td) / local
            clone = subprocess.run(
                ["git", "clone", "--depth", "1", "--quiet",
                 f"https://github.com/{repo}.git", str(dest)],
                capture_output=True, text=True)
            if clone.returncode != 0:
                print(f"{local}: cannot clone {repo}: {clone.stderr.strip()[:200]}")
                return 2
            mine, theirs = tracked_files(here), tracked_files(dest)
            only_mine = sorted(set(mine) - set(theirs))
            only_theirs = sorted(set(theirs) - set(mine))
            changed = sorted(k for k in set(mine) & set(theirs) if mine[k] != theirs[k])
            if not (only_mine or only_theirs or changed):
                print(f"{local}: in sync with {repo}")
                continue
            drift += 1
            print(f"{local}: DRIFT vs {repo} "
                  f"({len(changed)} changed, {len(only_mine)} local-only, "
                  f"{len(only_theirs)} upstream-only)")
            for name in changed[:15]:
                print(f"  changed  {name}")
            for name in only_mine[:10]:
                print(f"  local    {name}")
            for name in only_theirs[:10]:
                print(f"  upstream {name}")
    return 1 if drift else 0


if __name__ == "__main__":
    sys.exit(main())
