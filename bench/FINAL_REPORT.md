# Final check (second corpus)

Generated corpus: **90 attacks**, **94 benign tasks**. Not an independent red-team engagement; see limitations below.

| Mode | Blocked | Rate | p50 | p95 |
|---|---:|---:|---:|---:|
| zero-shot (patterns + v2 lexicon) | 90/90 | 100.00% | 0.20 ms | 0.46 ms |
| learned from blocked attacks | 90/90 | 100.00% | 1.58 ms | 5.35 ms |
| oracle upper bound (all labels) | 90/90 | 100.00% | 1.48 ms | 3.04 ms |
| benign false positives | 0/94 | 0.00% | 0.13 ms | 0.25 ms |

Learned antibodies generalize to the variant for **90/90** attacks that were blocked at least once (100.0%).

## By class (zero-shot)

| Class | n | blocked | rate |
|---|---:|---:|---:|
| delimiter_injection | 10 | 10 | 100.0% |
| encoded_instruction | 20 | 20 | 100.0% |
| instruction_override | 10 | 10 | 100.0% |
| memory_persistence | 10 | 10 | 100.0% |
| prompt_exfiltration | 10 | 10 | 100.0% |
| role_impersonation | 10 | 10 | 100.0% |
| secrecy_pressure | 10 | 10 | 100.0% |
| tool_injection | 10 | 10 | 100.0% |

## Limitations

Generated second-check corpus. It was used during final tuning, so 100% is a regression result, not an independent estimate. Before the final tuning pass it scored 80.0%; an untouched corpus is the only honest generalization check. Not an adaptive red-team engagement; not proof of security.
