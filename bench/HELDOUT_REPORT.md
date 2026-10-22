# Development corpus (v1 held-out, now used for v2)

Generated corpus: **200 attacks**, **154 benign tasks**. Not an independent red-team engagement; see limitations below.

> This corpus was held out for v1. The v2 lexicon was developed with it in view, so **100% is a development number**. The second check is in [FINAL_REPORT.md](FINAL_REPORT.md).

| Mode | Blocked | Rate | p50 | p95 |
|---|---:|---:|---:|---:|
| zero-shot (patterns + v2 lexicon) | 200/200 | 100.00% | 0.20 ms | 0.39 ms |
| learned from blocked attacks | 200/200 | 100.00% | 2.10 ms | 4.81 ms |
| oracle upper bound (all labels) | 200/200 | 100.00% | 2.02 ms | 4.82 ms |
| benign false positives | 0/154 | 0.00% | 0.15 ms | 0.23 ms |

Learned antibodies generalize to the variant for **200/200** attacks that were blocked at least once (100.0%).

## By class (zero-shot)

| Class | n | blocked | rate |
|---|---:|---:|---:|
| delimiter_injection | 15 | 15 | 100.0% |
| encoded_instruction | 20 | 20 | 100.0% |
| homoglyph_evasion | 11 | 11 | 100.0% |
| instruction_override | 26 | 26 | 100.0% |
| memory_persistence | 21 | 21 | 100.0% |
| payload_splitting | 15 | 15 | 100.0% |
| prompt_exfiltration | 21 | 21 | 100.0% |
| role_impersonation | 25 | 25 | 100.0% |
| secrecy_pressure | 20 | 20 | 100.0% |
| tool_injection | 26 | 26 | 100.0% |

## Limitations

The v1 corpus was originally held out, but v2 was developed and tuned against it. 100% is a development/regression result, not an independent estimate. An untouched corpus is the only honest generalization check; an adaptive attacker is not covered.
