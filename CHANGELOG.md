# Changelog

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
