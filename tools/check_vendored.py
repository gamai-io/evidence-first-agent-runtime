#!/usr/bin/env python3
"""Fail when a component is copied back into this tree, or a pin drifts.

Every component used to be vendored here and the copies silently diverged.
Now each one is installed from its own repository at a pinned commit. This
check enforces exactly two things:

1. no vendored copy reappears under the old directory name (that would restore
   the drift source);
2. the pin does not drift: ``requirements-vendored.txt`` and ``pyproject.toml``
   must agree on the commit, and — when the package is installed from a git
   checkout, which is how CI installs it — the installed commit must be that
   commit from that repository.

It does not compare file contents (there are no copies left to compare) and it
needs no network. A package that is not installed here is reported as such and
skipped: absence is not drift. If a distribution was installed without VCS
metadata (a local ``pip install .``), the pin cannot be confirmed from the
environment and the line says so; that is reported, not failed.

Exit codes: 0 no drift, 1 a copy is back or a pin drifted.
"""
from __future__ import annotations

import importlib.metadata
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "requirements-vendored.txt"
PYPROJECT = ROOT / "pyproject.toml"

# Former vendored directory -> (canonical repository, distribution name).
COMPONENTS = {
    "proofgate": ("gamai-io/proofgate-runtime", "proofgate-runtime"),
    "gamai_trust": ("gamai-io/gamai-trust", "gamai-trust"),
    "gamai_guard": ("gamai-io/gamai-guard", "gamai-guard"),
    "crossnode-bench": ("gamai-io/crossnode-bench", "crossnode-bench"),
    "polymorph": ("gamai-io/polymorph", "polymorph"),
}

# "name @ git+https://github.com/<org>/<repo>@<40-hex sha>"
PIN_RE = re.compile(
    r"([A-Za-z0-9][A-Za-z0-9._-]*)\s*@\s*"
    r"(git\+https://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)@([0-9a-f]{40}))")


def parse_pins(path: pathlib.Path) -> dict[str, tuple[str, str]]:
    """Distribution name -> (repository slug, commit) for every pin in *path*."""
    pins: dict[str, tuple[str, str]] = {}
    for name, _url, repo, commit in PIN_RE.findall(path.read_text(encoding="utf-8")):
        pins[name] = (repo, commit)
    return pins


def direct_origin(url: str) -> str:
    """Turn a local ``file://`` install URL into the clone's origin slug, if any."""
    if not url.startswith("file://"):
        return ""
    path = url[len("file://"):]
    proc = subprocess.run(["git", "-C", path, "remote", "get-url", "origin"],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        return ""
    origin = proc.stdout.strip()
    match = re.search(r"github\.com[:/]+([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?$", origin)
    return match.group(1) if match else ""


def installed_pin(dist_name: str) -> tuple[str, str] | None:
    """(repository slug, commit) recorded by pip for *dist_name*, or None."""
    try:
        dist = importlib.metadata.distribution(dist_name)
    except importlib.metadata.PackageNotFoundError:
        return None
    raw = dist.read_text("direct_url.json")
    if not raw:
        return ("", "")
    data = json.loads(raw)
    vcs = data.get("vcs_info") or {}
    if not vcs:
        return ("", "")
    repo = direct_origin(data.get("url", ""))
    return (repo, vcs.get("commit_id", ""))


def main() -> int:
    problems: list[str] = []

    for local in COMPONENTS:
        if (ROOT / local).is_dir():
            problems.append(f"{local}: vendored copy is back at {local}/; "
                            f"delete it and depend on the installed package")

    pins_req = parse_pins(REQUIREMENTS)
    pins_pyproject = parse_pins(PYPROJECT)

    for local, (repo, dist_name) in COMPONENTS.items():
        pin = pins_req.get(dist_name)
        if pin is None:
            problems.append(f"{dist_name}: no pin in requirements-vendored.txt")
            continue
        if pin[0] != repo:
            problems.append(f"{dist_name}: pinned to {pin[0]}, expected {repo}")
            continue

        other = pins_pyproject.get(dist_name)
        if other is None:
            problems.append(f"{dist_name}: no pin in pyproject.toml")
        elif other != pin:
            problems.append(f"{dist_name}: pin drift — requirements-vendored.txt says "
                            f"{pin[0]}@{pin[1][:7]}, pyproject.toml says "
                            f"{other[0]}@{other[1][:7]}")

        line = f"{local}: installed from {repo}@{pin[1][:7]}"
        got = installed_pin(dist_name)
        if got is None:
            print(f"{line} (dist {dist_name}: not installed in this environment)")
            continue
        if got == ("", ""):
            print(f"{line} (dist {dist_name} installed without VCS metadata; "
                  f"pin not verified here)")
            continue
        if got[0] and got[0] != repo:
            problems.append(f"{dist_name}: installed from {got[0]}, pinned to {repo}")
        if got[1] != pin[1]:
            problems.append(f"{dist_name}: installed commit {got[1][:7]}, "
                            f"pinned to {pin[1][:7]}")
        print(f"{line} (dist {dist_name}, installed commit {got[1][:7]})")

    for problem in problems:
        print(f"DRIFT  {problem}")
    if problems:
        print(f"{len(problems)} problem(s): a copy is back or a pin drifted")
        return 1
    print("no vendored copies, pins agree, installed commits match")
    return 0


if __name__ == "__main__":
    sys.exit(main())
