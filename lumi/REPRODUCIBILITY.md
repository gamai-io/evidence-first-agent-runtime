# Reproducibility, limits, and what the numbers mean

This file addresses review feedback on the LUMI benchmark. It states what is proven,
what is not, and how to reproduce each claim.

## Guard versions are separate commits (tags)

| Tag | Commit | Change | 1k result |
|---|---|---|---|
| guard-v1 | 100c7db | first deterministic guard (risk T1/T2 + injection/env) | 7/1000 (0.7%) |
| guard-v2 | 2fcf733 | + percent math (Decimal half-up) | 1/1000 (0.1%) |
| guard-v3 | 013cf64 | + mass-mail clarification | 0/1000 (PASS) |

Reproduce: `git checkout guard-v2` and run `bench_v2/run_bench.py --guard ...`.

## What the 10k rerun actually shows

| Job | Run | Result |
|---|---|---|
| 23443977 | 10k guard v3, 2026-11-03 | 0/10000 - not reproduced |
| 23453363 | 10k guard v3, 2026-11-04 | 1/10000 (0.01%) -> FAIL (strict); TTFT p50 3.61 s; total p95 13.41 s |
| 23442528 | 10k model-only, 2026-11-03 | 1683/10000 (16.8%) false-success |

Do not claim deterministic zero for the end-to-end scored run.

## Model-only vs guard-assisted

Report both columns. A guard answer is not an LLM answer: model-only rows can fail;
guard-assisted rows were blocked before any model call (0 tokens). Mixing them overstates
model quality. Split using the guard markers in the raw JSONL.

## Known limitations (unfixed)

1. Only 12 distinct tasks; 10k rows repeat them (stability, not breadth).
2. `check_results.py` checks expected text/number presence, not semantics.
3. Raw JSONL and LUMI logs are not committed. They live on LUMI under
   `/project/project_465003647/gama/out/guard_10000_<job>.jsonl` and require a valid EFP
   certificate to export. `lumi/verify_raw.py` verifies the exported file.
4. `verified=true` must be backed by a file/hash check; the benchmark alone does not prove
   downstream evidence handling.
