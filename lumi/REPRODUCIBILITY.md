# Reproducibility, limits, and what the numbers mean

This file addresses review feedback on the LUMI benchmark. It states plainly what is
proven, what is not, and how to reproduce each claim.

## Guard versions are separate commits (tags)

| Tag | Commit | Change | 1k result |
|---|---|---|---|
|  |  | first deterministic guard (risk T1/T2 + injection/env) | 7/1000 false-success (0.7%) |
|  |  | + percent math (Decimal half-up) | 1/1000 (0.1%) |
|  |  | + mass-mail clarification | 0/1000 (PASS) |

Reproduce a version:  and run .
The tags exist so the three implementations are not a single moving file.

## What the 10k rerun actually shows

| Job | Run | Result |
|---|---|---|
| 23443977 | 10k guard v3, 2026-11-03 | 0/10000 — **not reproduced** |
| 23453363 | 10k guard v3, 2026-11-04 | **1/10000 (0.01%) → FAIL (strict)**; TTFT p50 3.61 s; total p95 13.41 s |
| 23442528 | 10k model-only, 2026-11-03 | 1683/10000 (16.8%) false-success |

Do not claim deterministic zero for the end-to-end scored run. The guard is deterministic;
the scored benchmark is not error-free.

## Model-only vs guard-assisted

Report both columns. A guard answer is not an LLM answer:

- model-only: model receives the prompt and can fail.
- guard-assisted: blocked/answered deterministically before any model call (0 tokens).

Mixing them into one "false-success" number overstates model quality. Use the raw JSONL
field /guard markers to split.

## Known limitations (unfixed)

1. The prompt set has only 12 distinct tasks; 10k rows repeat them. This measures stability,
   not breadth.
2.  verifies expected text/number presence; it is not a semantic judge.
3. Raw JSONL and LUMI logs are not committed. They live on LUMI:
    (jobs above), and must be
   exported with a valid EFP certificate.  verifies an exported file.
4.  in app code must be backed by a file/hash check; the benchmark alone does
   not prove downstream evidence handling.
