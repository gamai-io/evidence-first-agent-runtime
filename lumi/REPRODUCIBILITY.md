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



## Raw results (published)

| Job | rows | distinct prompts | duplicate rows | false-success | sha256 of .jsonl | file |
|---|---|---|---|---|---|---|
| 23453363 | 10000 | 12 | 9988 | 1 (0.01%) | 3c3352718fe10994901c9d0ccecccf534eb56ffdf2ccc163fcf073bc41d72a6e | https://github.com/gamai-io/gama-lumi-bench/releases/download/v0.1.0/guard_10000_23453363.jsonl.gz |
| 23443977 | 10000 | 12 | 9988 | 0 | d6ce6fcbe10cb473bd3ba9c443410965b55bd469927080f0f370758ecacc973c | https://github.com/gamai-io/gama-lumi-bench/releases/download/v0.1.0/guard_10000_23443977.jsonl.gz |

The 12 distinct tasks are repeated 10,000 times: these raw files measure stability, not
breadth. Verify any download with `python3 lumi/verify_raw.py <file> --expect-n 10000`.



## Distinct-task set v2 (unbenchmarked)

`bench_v2/prompts_v2.json` adds 110 new tasks (30 fact, 30 math, 22 string, 15 safety,
13 honesty) for 122 distinct tasks total. It is **not benchmarked yet**: LUMI GPU was busy
with a training job on 2026-11-04. Run with:
`python3 run_bench.py --prompts prompts_v2.json --set model_plane_v2 ...`

## Known limitations (unfixed)

1. v1 has only 12 distinct tasks (10k rows repeat them). v2 adds 110 distinct tasks but is not yet run.
2. `check_results.py` checks expected text/number presence, not semantics.
3. Raw JSONL is published as gzip release assets (above); full LUMI logs are not. `lumi/verify_raw.py` verifies the exported file.
4. `verified=true` must be backed by a file/hash check; the benchmark alone does not prove
   downstream evidence handling.
