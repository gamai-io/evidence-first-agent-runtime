# Migration: five vendored copies -> five pinned installs

This harness used to carry copies of five packages. Every copy drifted, because
nothing forced it to stay in step with the repository it came from. All five are
now installed from their own repositories at a pinned commit; no component code
lives in this tree.

| Directory (removed) | Now installed as | Pinned commit | Why it used to be copied |
|---|---|---|---|
| `proofgate/` | `proofgate-runtime` | `6ad4e0b1e807cfe47bda1e892b022d3db05a0bde` | no packaging metadata |
| `gamai_trust/` | `gamai-trust` | `936a2cb505bceb5308b2ccba85204aeba72353af` | no packaging metadata |
| `gamai_guard/` | `gamai-guard` | `1fa20420eb3ec5e957d88d1f7f5a689cc8dc59a9` | no packaging metadata |
| `crossnode-bench/` | `crossnode-bench` | `33b8369d4a6e43a4f9c6bf2afef3dea850dea284` | no `pyproject.toml`/`setup.py` upstream |
| `polymorph/` | `polymorph` | `2d8bdf8c2f242f7d8cb74fdc888548f9f6cb4b18` | no `pyproject.toml`/`setup.py` upstream |

## Why crossnode-bench and polymorph were stuck

`pip install git+https://github.com/gamai-io/<repo>` failed with *"does not
appear to be a Python project: neither 'setup.py' nor 'pyproject.toml' found"*.
The copies were therefore kept as pinned snapshots, and a weekly job compared
their Python files against upstream to catch drift.

Both repositories now ship packaging that changes no behaviour:

- **crossnode-bench** — `pyproject.toml` (setuptools, one `py-modules` entry,
  version 1.7.0 as the README and the tag claim, `requires-python >= 3.10`, no
  runtime dependencies) and a `crossnode` console script that calls the
  existing `main()`. The wheel contains `crossnode.py` only; `dataset/`,
  `results/` and `paper/` are archive material and stay in the repository.
- **polymorph** — `pyproject.toml` with the eight existing top-level modules as
  `py-modules` (so `import effect_lease`/`import safe_exec` still work, no
  import renames), version 0.1.0 (its only tag), `requires-python >= 3.10`.
  `corpus/` (68 KB) ships as package data: the modules resolve it as
  `Path(__file__).parent / "corpus"`, so installing it beside the modules keeps
  that resolution working without touching the code, and without it the wheel
  cannot run `run_e1`/`e3_cross_language`. The test that executes
  `safe_exec.py` now runs the imported module (`Path(safe_exec.__file__)`), so
  it passes from a wheel too.

Both were verified by building a wheel, installing it into a fresh venv and
running the entry points and test suite with the source tree absent.

## The two local adaptations moved into this repository

The copies were not byte-identical to upstream; each carried one adaptation.
Both are now umbrella code:

1. **`FleetNode` and `CliNode`** (plus the `gama-cli` and `fleet` node types in
   the config loader) lived inside the vendored `crossnode.py`. They are in
   [`bench/crossnode_fleet/fleet_nodes.py`](../bench/crossnode_fleet/fleet_nodes.py)
   and subclass the installed `crossnode.Node`. The fleet runner scripts
   (`real1000*.py`, `scale1000.py`) moved next to them in
   [`bench/crossnode_fleet/`](../bench/crossnode_fleet/), with their import
   changed to `from fleet_nodes import CliNode`. The benchmark itself is
   upstream, unmodified.
2. **The `agent-immunity` path for polymorph's E3 probe.** Upstream
   `e3_cross_language.py` imports `immunity` from `agent-immunity/` next to
   itself; in this tree that directory is a separate component. The vendored
   copy pointed at `../agent-immunity`. The path fix now lives in
   [`bench/polymorph_e3.py`](../bench/polymorph_e3.py), which puts this
   repository's `agent-immunity/` on `sys.path` and runs the installed
   `e3_cross_language` as `__main__`. The two `immunity.py` files were
   byte-identical at the pinned commits, so the result is the same.

## Command changes

| Before (vendored) | Now (installed) |
|---|---|
| `python3 crossnode-bench/crossnode.py --demo` | `python3 -m crossnode --demo` (or `crossnode --demo`) |
| `python3 crossnode-bench/tests/run_tests.py` | the component's own pytest suite lives upstream; this repo asserts the demo invariants in `repro.sh` and `tests/test_installed_components.py` |
| `python3 polymorph/run_e1.py` | `python3 -m run_e1` |
| `python3 polymorph/run_e2.py` | `python3 -m run_e2` |
| `python3 polymorph/e3_cross_language.py` | `python3 bench/polymorph_e3.py` |
| `python3 polymorph/tests/test_safe_exec.py` | `python3 -m pytest tests/test_installed_components.py -q` |

`repro.sh` uses the installed commands only. Component unit tests
(`crossnode`'s 105 scorer tests, polymorph's 15/15 + 3/3 + 5/5) live in and run
from their own repositories; this harness pins the behaviour it consumes.

## What `tools/check_vendored.py` enforces

It no longer compares file contents (there are no copies to compare). It fails
if, and only if:

1. one of the five directories reappears under its old name, or
2. a pin drifts: `requirements-vendored.txt` and `pyproject.toml` disagree on the
   repository or commit, or the installed distribution records a different
   commit from the pinned one.

A package that is not installed in the current environment is reported as such
and skipped; installation without VCS metadata is reported but not failed, since
the pin cannot be read from the environment. No network is needed.

## Historical documents

Dated lab notes (`docs/E1_RESULTS_*`, `E2_*`, `E3_*`, `E4_*`, `E5_*`,
`TOCTOU_*`, `POLYMORPH_PLAN.md`) keep the paths they were written with; they
record runs made when the directories existed. The current reproduction commands
are in `README.md`, `repro.sh` and `docs/EVIDENCE.md`.
