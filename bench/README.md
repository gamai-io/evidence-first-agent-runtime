# GAMA trust-layer & bench results (2026-11-05)

All numbers below are produced by the scripts in `bench/tools/` (proofgate from this repo)
and the raw JSON is in `bench/results/` (sha256 in `bench/SHA256SUMS`).

## Trust-layer stress (adversarial)
| test | scope | result |
|---|---|---|
| `trust_stress_10k.json` | 10k adversarial claims | 10000/10000 match, **0 false-accept**, 0 false-refute, tamper 5512/5512, avg 0.036 ms |
| `parallel_scaling.json` | 50k→10M, 1–128 workers | up to **1.54M checks/s** on 1 node (128 cores), 0 exceptions |
| `trust_stress_400m.json` | **400,000,000** checks | 16 nodes (4 jobs × 4×128 cores), wall **16.77 s**, **24.41M checks/s** aggregate, **0 exceptions**, **0 bad status**, **0 tampered report accepted**, 2.43M tamper probes |

Known open item: nondeterminism in 66/400M recomputations (0.0000165%) — being traced; all other invariants clean.

## Multi-agent reliability
`multiagent_10k.json`: 200 agents × 50 claims (corruption 0/5/20/50%):
**0 false-accept**, detection **100%** per group, 100% good confirmed, 32.5k claims/s.

## Reproducing
```
python3 bench/tools/trust_stress.py          # 10k adversarial suite (LUMI: python3.11)
python3 bench/tools/make_pack.py --run-jsonl results.jsonl --prompts bench/tools/prompts_v2.json --out pack
python3 bench/tools/grade.py --jsonl results.jsonl --prompts bench/tools/prompts_v2.json --md report.md
```
Guard is never counted as model: `mode=model` vs `mode=harness` are reported separately.
