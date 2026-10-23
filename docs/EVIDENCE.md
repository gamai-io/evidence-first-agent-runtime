# Evidence index

Every public number should be traceable to a command, a commit and an
artifact. This index is deliberately short; the full claims ledger is in
[`launch/claims.md`](../launch/claims.md).

| Claim | Command | Artifact | Limitation |
|---|---|---|---|
| proofgate demo: 10 confirmed, 2 refuted, 0 unverified | `python3 proofgate/proofgate.py demo` | `/tmp/proofgate_demo.json` | 12 built-in claims; predicates are caller-supplied |
| Reports are tamper-evident | `python3 proofgate/tests/run_tests.py` | test output | A hash proves integrity, not authenticity |
| Provenance signatures detect tampering | `python3 proofgate/tests/test_provenance.py` | 9/9 tests | Does not prove the source was truthful |
| Built-in injection suite: 100% -> 0% | `python3 agent-immunity/eval.py` | `agent-immunity/eval_results.json` (generated; not tracked) | Synthetic corpus; not an adaptive attacker |
| Development zero-shot: 100% (tuned) | `python3 bench/run_heldout.py` | `bench/heldout_results.json`, `bench/HELDOUT_REPORT.md` | v2 was tuned on this corpus; 100% is a regression, not independent |
| Second-corpus zero-shot: 100% (tuned; 80% before tuning) | `python3 bench/run_final.py` | `bench/final_results.json`, `bench/FINAL_REPORT.md` | Also used in final tuning; pre-tuning was 80%; not an adaptive red team |
| Learned variants: 200/200 dev, 90/90 second check | both runs | both reports | Only attacks blocked once can be learned |
| Benign false positives: 0/154 dev, 0/94 second check | both runs | both reports | Small, English/Bosnian benign set |
| Edge-corpus zero-shot: 100% (tuned) | `python3 bench/run_edge.py` | `bench/edge_results.json`, `bench/EDGE_REPORT.md` | Also used during tuning; not independent |
| German cross-language holdout: 1/30 (3.3%), 0/15 benign FP | `python3 polymorph/e3_cross_language.py` | `polymorph/corpus/e3_results.json`, `docs/E3_RESULTS_2026-10-22.md` | Human-authored German, not adaptive; shows filter is language-specific |
| German semantic gate: tuned 28/30, fresh 6/12 (50%) | `python3 polymorph/semantic_gate.py` | `polymorph/corpus/e4_results.json`, `docs/E4_RESULTS_2026-10-22.md` | Prompt leakage and tuned guards; embedding cascade 10/12; not a boundary |
| TOCTOU: 5/5 swaps allowed before exec; safe_exec denies 5/5 | `/tmp/toctou` lab; `polymorph/safe_exec.py` | `docs/TOCTOU_RESULTS_2026-10-22.md` | Shell scope; no ELF/argv/env binding yet |
| CBR before gate: 131 qualifying, 120 pending, 2 timers stopped (historical) | read-only SQL + systemd | `docs/SECURITY_ALERT_CBR_2026-10-22.md` | Superseded by the live 0-promotion/58-review row; no data deleted |
| GAMA Guard tests: 7/7 | `python3 gamai_guard/tests/run_tests.py` | test output | Unit scope; not an adaptive attacker |
| Blind multilingual: lexical 4/30, embedding 29/30, 0/10 FP | `python3 labs/eval_blind.py` | `labs/blind_multilingual_results.json` | 30 human attacks; one wording miss; CPU 55 s / GTX 1660S 3.31 s |
| Guard worker: 40 texts in 1.37 s, 29/30, 0 FP | `POST localhost:8091/check_many` | `docs/GUARD_WORKER_2026-10-23.md` | VM-only; 127.0.0.1; serialized GPU batch |
| Executed-byte binding: admitted SHA = executed SHA | `python3 polymorph/tests/test_safe_exec.py` | 3/3 tests; `polymorph/safe_exec.py --receipt` | Shell scope; no ELF/argv/env binding |
| CBR gate: 0 automatic promotions, 58 unique review; dual control | live `/opt/gama-harness/gama_cbr_promote.py` dry-run | `_cbr_review.jsonl`, `_cbr_approvals.json` | Operator path; approval key custody external |
| I Ching/codon: r=1 is a tautology | `python3 labs/iching_codons.py` | `labs/iching_codons_results.json` | 6-bit mapping is distance-preserving; non-identifiable |
| Agent-immunity tests: 40/40 | `python3 agent-immunity/tests/run_tests.py` | test output | Stdlib only; no adaptive attacker |
| crossnode-bench: 46/48, 2 false successes | `python3 crossnode-bench/crossnode.py --demo --runs 1` | `crossnode-bench/runs/<stamp>/report.json` | Demo uses mocked lying nodes; fleet run is separate |
| CI runs on Python 3.10/3.11/3.12 | `.github/workflows/ci.yml` | GitHub Actions run | Hosted runner, public logs only |
| MCP server exposes 5 tools | `python3 -m gamai_trust.mcp_server --selftest` | `mcp selftest ok: 5 tools` | No transport authentication; stdio only |

## Reproduce everything

```bash
./repro.sh
```

This runs the component tests, the provenance tests, the MCP selftest, a
20-attack benchmark smoke test, and both demos. It needs no network, database,
or API keys.

## What is deliberately not claimed

- No "state of the art" claim.
- No "unhackable" or "solves prompt injection" claim.
- No claim that the generated corpora are independent red-team engagements.
- No claim that the demo's mocked lying nodes are a production fleet.
- No claim that a signature proves the evidence is true.
