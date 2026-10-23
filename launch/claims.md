# Claims ledger

Every public number must be traceable to a command and bounded by a
limitation. If a claim is not in this table, it does not go in a post.

| # | Claim | Evidence | N / corpus | Limitation | What would falsify it |
|---|---|---|---|---|---|
| 1 | A gate can return `refuted`/`unverified` instead of a confident false "done" | `python3 proofgate/proofgate.py demo` → `confirmed=10, refuted=2, unverified=0` | 12 built-in claims | Predicates are caller-supplied; semantic truth is not checked | Demo returns all confirmed, or missing evidence is confirmed |
| 2 | Reports are tamper-evident | `verify(report)` after mutating one value → `tampered=true` | 16 tests | The verifier trusts the hash algorithm, not the observer | Mutation still verifies as ok |
| 3 | Injection success drops from 100% to 0% in 3 rounds **on the built-in suite** | `python3 agent-immunity/eval.py` | 10 payloads × 3 channels × 3 rounds; 20 benign | Synthetic corpus; lexical near-miss; not an adaptive attacker. The tuned corpora reach 100%, but the second corpus was 80% before the final tuning pass; this is not a general protection claim. | ASR stays >0 in rounds 2–3, or utility drops / false denial rises materially |
| 4 | Filter-only leaves a gap | same eval, `taint_only` row | same | The reworded variant is ours; other variants may behave differently | Filter-only ASR is 0 in all rounds |
| 5 | Guard overhead is ~1.3 ms | generated `eval_results.json` → `guard_p50_ms` | 90 checks per round | Python, single process, warm SQLite | p50 > 10 ms in a clean run |
| 6 | Cross-node benchmark detects false success | `python3 crossnode-bench/crossnode.py --demo` → 46/48, 2 false successes | 16 tasks × 3 nodes | Demo uses mocked lies; real fleet run is separate | Demo reports 48/48, or the two lies are not named |
| 7 | Real fleet reproduced 3 false-success classes | reference run, sanitized (missing program, missing app, Session 0) | 6 nodes × 16 tasks × 3 runs, 14/16 per run | Node names/addresses removed; not independently reproduced yet | A rerun on the same fleet cannot reproduce the classes |
| 8 | Runtime context: 202 tools, 18/18 MCP, 8 plugins, 0 degraded | live `/health` snapshot | one host, one moment | Not a benchmark; a configuration snapshot | A fresh `/health` shows degraded or fewer live MCP servers |
| 9 | Code bench 6/6 at ~2.0 s/task | internal bench, 6 tasks | 6 tasks, our hidden tests | Small N, single model, our tasks | Rerun on the public harness fails >0 tasks or is much slower |
| 10 | pass@1 = pass@3 = 1.0; $0.00172/solved | internal pass@k runner, 20 tasks, n=3 | 60 attempts | Our tasks; cost depends on provider pricing | Rerun yields <1.0 or cost differs by >2× |
| 11 | Development zero-shot block rate is 100% after tuning | `python3 bench/run_heldout.py` | 200 generated attacks / 154 benign | v2 was tuned on this corpus; not independent | A clean rerun differs by >5 points |
| 12 | Second-corpus zero-shot block rate is 100% after tuning (80.0% before tuning) | `python3 bench/run_final.py` | 90 attacks / 94 benign | Used in final tuning; not independent; no adaptive red team | A clean rerun differs by >5 points, or an independent corpus gives a much lower rate |
| 12b | Learned antibodies block 200/200 dev variants and 90/90 second-check variants that were blocked once | both runs, `learnable_variant_rate_pct` | learnable attacks only | Only attacks already blocked can be learned; oracle upper bound is 100%/97.8% | The rate drops materially on a fresh corpus or after decay |
| 13 | CI runs the full repro on every push | `.github/workflows/ci.yml` | Python 3.10/3.11/3.12 | GitHub-hosted runner, public logs only | Workflow fails or is disabled |
| 14 | Provenance signatures detect tampering | `proofgate/tests/test_provenance.py` | 9 tests (HMAC + Ed25519) | Proves integrity/authenticity, **not** source truthfulness; key custody is external | A mutated signed report still verifies |
| 15 | Pricing tiers are proposed, not validated | README "gamAI Trust Layer" section | none | Hypotheses; no buyer tests | Buyer research contradicts the ranges |
| 16 | A strict plan gate denies effect/scope widening before execution | `python3 gamai_guard/tests/run_tests.py` → 7/7 | 7 unit tests | Static plan; `safe_exec` covers runtime TOCTOU | A widened effect/scope passes admission, or a malformed plan is admitted |
| 17 | A multilingual embedding cascade recovers attacks the lexical filter misses | `python3 labs/eval_blind.py` → lexical 4/30, embedding 29/30, 0/10 FP | 30 attacks + 10 benign (DE/FR/ES/BS) | Human-authored; one wording miss; CPU 55 s / GPU 3.31 s; prototypes cached | A fresh blind corpus stays near 13% or FP >0 |
| 18 | Executed bytes are bound to the admitted bytes | `python3 polymorph/tests/test_safe_exec.py` → 3/3 | 3 TOCTOU/PATH cases | Shell scripts only | A swapped file executes while the receipt still verifies |
| 19 | CBR promotion requires proposer≠approver and evidence | live dry-run → 0 promotions, 58 review | 58 unique cases | Operator path; HMAC key custody external | A risky goal is promoted with `GAMA_CBR_APPROVE=1` alone |
| 20 | 64 hexagrams vs 64 codons is not evidence | `python3 labs/iching_codons.py` → r=1.0, tautology | 64×64, 10k permutations | 6-bit mapping is distance-preserving; non-identifiable | A pre-registered, out-of-sample mapping survives |
| 21 | CGR box-counting is not a strong genome signature | `python3 labs/kmer_fractal.py` → D 1.73–1.98; Δ≤0.024 | 4 genomes, 5 shuffles | Mononucleotide shuffle; no dinucleotide control | A dinucleotide-preserving control still leaves a large, stable gap |
| 22 | A broad bibliometric count does not validate an occult/wellness claim | `python3 labs/claims_audit.py` → 327–140,663 hits, top hits irrelevant | 10 claims, OpenAlex top-3 | Editorial verdicts; not a systematic review | A pre-registered, precise query set with primary-source appraisal reverses a verdict |

## Rules for using this table

- Always say "on our corpus/tasks" next to a percentage.
- Never say "state of the art", "solves prompt injection", or "unhackable".
- If an external user reports a counterexample, add a row; do not delete the
  old one.
- Re-run the command before publishing; numbers drift with code and provider.
