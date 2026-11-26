#!/usr/bin/env python3
"""Fail when a vendored component has drifted from its standalone repository.

Most components used to be copied into this tree, and the copies silently
diverged. They are now installed from their own repositories instead. Two
components cannot be installed because their upstream repositories ship no
``pyproject.toml``/``setup.py``; those stay here as pinned snapshots.

This check therefore does two things:

* for installed components, it fails if the vendored directory comes back
  (that would re-introduce the drift source);
* for the two pinned snapshots, it clones the upstream repository at the pinned
  commit and compares the Python files. A file that differs is drift unless it
  is an explicitly recorded local divergence; the recorded local and upstream
  hashes make sure an exception is re-reviewed when either side changes.

Directories that no longer exist are reported as "not vendored" and skipped.
Network is required for the snapshot comparison, so this runs on a schedule and
on demand, not on every push.

Exit codes: 0 no unexpected drift, 1 drift found, 2 the check itself could not run.
"""
from __future__ import annotations

import hashlib
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]

# Vendored directory -> (standalone repository, pinned commit).
# These have no packaging metadata upstream, so pip cannot install them.
VENDORED = {
    "crossnode-bench": (
        "gamai-io/crossnode-bench",
        "962977072059ea5ba13dad2114c71d40dcb62f95",
    ),
    "polymorph": (
        "gamai-io/polymorph",
        "2e3778014bc35d47b7d2d405ce78bdf56078aae0",
    ),
}

# Former vendored directories -> (standalone repository, install name).
# They are dependencies now: tools/check_vendored.py fails if a copy reappears.
DEPENDENCIES = {
    "proofgate": ("gamai-io/proofgate-runtime", "proofgate-runtime"),
    "gamai_trust": ("gamai-io/gamai-trust", "gamai-trust"),
    "gamai_guard": ("gamai-io/gamai-guard", "gamai-guard"),
}

# Vendored file -> (local sha256, upstream sha256, reason).
# Both hashes must still match; otherwise the exception is stale and the weekly
# job asks for a human review instead of staying permanently green.
KNOWN_DIVERGENCE = {
    "crossnode-bench": {
        "crossnode.py": (
            "431a470cf9d32f47c3705d51ec3ac7255d2a171e5e26d3abd3749972f935409d",
            "c2191f1ce3b2c1110502162441d83114b4e375bb28b4e8aad07caa720167e2c5",
            "adds the FleetNode/CliNode adapters this umbrella uses",
        ),
    },
    "polymorph": {
        "e3_cross_language.py": (
            "2381978bfb5dc81839185920f4087f432a7a13370596bee468d25c6974927116",
            "512aab9970d39e26a84c56837bf23f0f5597208933920b55b82b4eaac248d61e",
            "resolves agent-immunity from the umbrella root",
        ),
    },
}

SKIP_NAMES = {".git", "__pycache__", ".pytest_cache", "node_modules"}
CODE_SUFFIXES = {".py"}


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def code_files(base: pathlib.Path) -> dict[str, str]:
    """Relative path -> sha256 for every Python file under *base*."""
    out: dict[str, str] = {}
    for path in base.rglob("*.py"):
        if not path.is_file():
            continue
        if any(part in SKIP_NAMES for part in path.parts):
            continue
        if path.suffix not in CODE_SUFFIXES:
            continue
        out[path.relative_to(base).as_posix()] = sha256(path)
    return out


def clone_at(repo: str, commit: str, dest: pathlib.Path) -> str | None:
    """Clone *repo* and check out *commit*. Returns an error string on failure."""
    clone = subprocess.run(
        ["git", "clone", "--quiet", f"https://github.com/{repo}.git", str(dest)],
        capture_output=True, text=True)
    if clone.returncode != 0:
        return clone.stderr.strip()[:200]
    checkout = subprocess.run(
        ["git", "-C", str(dest), "checkout", "--quiet", commit],
        capture_output=True, text=True)
    if checkout.returncode != 0:
        return checkout.stderr.strip()[:200]
    return None


def check_snapshot(local: str, repo: str, commit: str, workdir: pathlib.Path) -> int:
    here = ROOT / local
    if not here.is_dir():
        print(f"{local}: not vendored (skipped; pinned snapshot removed)")
        return 0

    dest = workdir / local
    error = clone_at(repo, commit, dest)
    if error:
        print(f"{local}: cannot clone {repo}@{commit[:7]}: {error}")
        return 2

    mine, theirs = code_files(here), code_files(dest)
    common = set(mine) & set(theirs)
    problems: list[str] = []
    print(f"{local}: pinned at {repo}@{commit[:7]} "
          f"({len(common)} code files compared, "
          f"{len(set(mine) - common)} local-only, "
          f"{len(set(theirs) - common)} upstream-only)")

    for name in sorted(common):
        if mine[name] == theirs[name]:
            continue
        allowed = KNOWN_DIVERGENCE.get(local, {}).get(name)
        if allowed:
            local_hash, upstream_hash, why = allowed
            if mine[name] == local_hash and theirs[name] == upstream_hash:
                print(f"  known divergence  {name} ({why})")
                continue
            if theirs[name] != upstream_hash:
                problems.append(
                    f"{name}: upstream changed since this divergence was recorded "
                    f"({why}); re-review it")
            if mine[name] != local_hash:
                problems.append(
                    f"{name}: local file changed since this divergence was recorded; "
                    f"update KNOWN_DIVERGENCE if the change is intentional")
            continue
        problems.append(f"{name}: differs from {repo}@{commit[:7]}")

    if problems:
        print(f"{local}: DRIFT")
        for problem in problems:
            print(f"  {problem}")
        return 1
    print(f"{local}: in sync")
    return 0


def main() -> int:
    drift = 0
    for local, (repo, package) in DEPENDENCIES.items():
        if (ROOT / local).is_dir():
            drift += 1
            print(f"{local}: UNEXPECTED vendored copy is back; "
                  f"depend on {package} ({repo}) and delete the directory")
        else:
            print(f"{local}: not vendored (installed from {repo} as {package})")

    with tempfile.TemporaryDirectory() as td:
        workdir = pathlib.Path(td)
        for local, (repo, commit) in VENDORED.items():
            result = check_snapshot(local, repo, commit, workdir)
            if result == 2:
                return 2
            drift += result

    return 1 if drift else 0


if __name__ == "__main__":
    sys.exit(main())
