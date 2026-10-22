# Claims ledger

Every public number must be traceable to a command and bounded by a
limitation. If a claim is not in this table, it does not go in a post.

| # | Claim | Evidence | N / corpus | Limitation | What would falsify it |
|---|---|---|---|---|---|
| 1 | A gate can return `refuted`/`unverified` instead of a confident false "done" | `python3 proofgate/proofgate.py demo` → `confirmed=10, refuted=2, unverified=0` | 12 built-in claims | Predicates are caller-supplied; semantic truth is not checked | Demo returns all confirmed, or missing evidence is confirmed |
| 2 | Reports are tamper-evident | `verify(report)` after mutating one value → `tampered=true` | 16 tests | The verifier trusts the hash algorithm, not the observer | Mutation still verifies as ok |
| 3 | Injection success drops from 100% to 0% in 3 rounds | `python3 agent-immunity/eval.py` | 10 payloads × 3 channels × 3 rounds; 20 benign | Synthetic corpus; lexical near-miss; not an adaptive attacker | ASR stays >0 in rounds 2–3, or utility drops / false denial rises materially |
| 4 | Filter-only leaves a gap | same eval, `taint_only` row | same | The reworded variant is ours; other variants may behave differently | Filter-only ASR is 0 in all rounds |
| 5 | Guard overhead is ~1.3 ms | `eval_results.json` → `guard_p50_ms` | 90 checks per round | Python, single process, warm SQLite | p50 > 10 ms in a clean run |
| 6 | Cross-node benchmark detects false success | `python3 crossnode-bench/crossnode.py --demo` → 46/48, 2 false successes | 16 tasks × 3 nodes | Demo uses mocked lies; real fleet run is separate | Demo reports 48/48, or the two lies are not named |
| 7 | Real fleet reproduced 3 false-success classes | reference run, sanitized (missing program, missing app, Session 0) | 6 nodes × 16 tasks × 3 runs, 14/16 per run | Node names/addresses removed; not independently reproduced yet | A rerun on the same fleet cannot reproduce the classes |
| 8 | Runtime context: 202 tools, 18/18 MCP, 8 plugins, 0 degraded | live `/health` snapshot | one host, one moment | Not a benchmark; a configuration snapshot | A fresh `/health` shows degraded or fewer live MCP servers |
| 9 | Code bench 6/6 at ~2.0 s/task | internal bench, 6 tasks | 6 tasks, our hidden tests | Small N, single model, our tasks | Rerun on the public harness fails >0 tasks or is much slower |
| 10 | pass@1 = pass@3 = 1.0; $0.00172/solved | internal pass@k runner, 20 tasks, n=3 | 60 attempts | Our tasks; cost depends on provider pricing | Rerun yields <1.0 or cost differs by >2× |

## Rules for using this table

- Always say "on our corpus/tasks" next to a percentage.
- Never say "state of the art", "solves prompt injection", or "unhackable".
- If an external user reports a counterexample, add a row; do not delete the
  old one.
- Re-run the command before publishing; numbers drift with code and provider.
