# Edge regression corpus

Generated corpus: **70 attacks**, **104 benign tasks**. Not an independent red-team engagement; see limitations below.

| Mode | Blocked | Rate | p50 | p95 |
|---|---:|---:|---:|---:|
| zero-shot (patterns + v2 lexicon) | 70/70 | 100.00% | 0.18 ms | 0.47 ms |
| learned from blocked attacks | 70/70 | 100.00% | 1.45 ms | 2.75 ms |
| oracle upper bound (all labels) | 70/70 | 100.00% | 1.24 ms | 2.08 ms |
| benign false positives | 0/104 | 0.00% | 0.11 ms | 0.25 ms |

Learned antibodies generalize to the variant for **70/70** attacks that were blocked at least once (100.0%).

## By class (zero-shot)

| Class | n | blocked | rate |
|---|---:|---:|---:|
| delimiter_injection | 10 | 10 | 100.0% |
| instruction_override | 10 | 10 | 100.0% |
| memory_persistence | 10 | 10 | 100.0% |
| prompt_exfiltration | 10 | 10 | 100.0% |
| role_impersonation | 10 | 10 | 100.0% |
| secrecy_pressure | 10 | 10 | 100.0% |
| tool_injection | 10 | 10 | 100.0% |

## Limitations

Edge regression corpus. It was used during tuning, so 100% is a regression result, not an independent estimate. Adaptive attackers are not covered.
