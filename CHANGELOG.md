# Changelog

## Unreleased

### Changed

- `crossnode-bench` and `polymorph` are installed instead of copied. Both
  upstream repositories now ship `pyproject.toml` (crossnode-bench 1.7.0,
  polymorph 0.1.0), so the vendored directories are gone and
  `requirements-vendored.txt` pins all five components.
- The two local adaptations moved into umbrella code: `FleetNode`/`CliNode`
  and the `gama-cli`/`fleet` config types live in `bench/crossnode_fleet/`
  (with the real-1000 runners), and polymorph's E3 `agent-immunity` path is in
  `bench/polymorph_e3.py`.
- `repro.sh` runs `python -m crossnode`, `python -m run_e1`, `python -m run_e2`
  and the E3 wrapper, and verifies the produced crossnode report.
- `tools/check_vendored.py` reports all five components as installed from
  `<repo>@<sha>` and fails only if a copy reappears or a pin drifts
  (requirements vs pyproject, or installed commit vs pin). No network needed;
  the weekly job now installs the pins first.
- New `tests/test_installed_components.py` pins the component contracts this
  harness relies on (25 passed, 2 skipped).
- Migration notes: `docs/MIGRATION.md`.

## 0.2.0 - 2026-10-22

### Added

- v2 lexical intent detector in `agent-immunity`: override, role, secrecy,
  memory, tool, exfiltration and delimiter features, plus base64/hex decoding.
- Context gates for quoted/test overrides, analytical questions, sandbox
  commands and benign UI/database tasks.
- `bench/gen_final.py`, `bench/run_final.py`, `bench/run_edge.py` and three
  generated corpora: development (200 attacks), second (90) and edge (70).
- `bench/benign_hard.jsonl` with 54 hard-negative benign probes.
- 12 new agent-immunity tests (40 total).
- `CHANGELOG.md`, `FINAL_REPORT.md`, `EDGE_REPORT.md` and regenerated
  development report.

### Changed

- Development corpus: 29.0% -> 100% zero-shot on the tuned corpus.
- Second corpus: 80.0% before final tuning -> 100% after tuning.
- Edge corpus: 70/70 zero-shot.
- Benign false positives: 0/352 across the three tuned corpora.
- Documentation now distinguishes tuned regression results from independent
  generalization; no adaptive red-team claim is made.

### Fixed

- Quoted/test override examples no longer trigger the shield.
- Benign SQL, migration, sandbox, cookie-persistence and UI strings no longer
  false-positive.
- Encoded role/override payloads are decoded and blocked.
