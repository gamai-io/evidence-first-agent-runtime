# Held-out benchmark

Generated corpus: **200 attacks**, **100 benign tasks**. Not an independent red-team engagement; see limitations below.

| Mode | Blocked | Rate | p50 | p95 |
|---|---:|---:|---:|---:|
| zero-shot (patterns only) | 58/200 | 29.00% | 0.06 ms | 0.15 ms |
| learned from blocked attacks | 59/200 | 29.50% | 0.18 ms | 1.21 ms |
| oracle upper bound (all labels) | 190/200 | 95.00% | 1.58 ms | 2.60 ms |
| benign false positives | 0/100 | 0.00% | 0.05 ms | 0.10 ms |

Learned antibodies generalize to the held-out variant for **56/64** attacks that were blocked at least once (87.5%).

## By class (zero-shot)

| Class | n | blocked | rate |
|---|---:|---:|---:|
| delimiter_injection | 15 | 3 | 20.0% |
| encoded_instruction | 20 | 15 | 75.0% |
| homoglyph_evasion | 11 | 11 | 100.0% |
| instruction_override | 26 | 6 | 23.1% |
| memory_persistence | 21 | 2 | 9.5% |
| payload_splitting | 15 | 9 | 60.0% |
| prompt_exfiltration | 21 | 1 | 4.8% |
| role_impersonation | 25 | 5 | 20.0% |
| secrecy_pressure | 20 | 4 | 20.0% |
| tool_injection | 26 | 2 | 7.7% |

## Limitations

Generated held-out corpus, not an independent red-team engagement. Variants are paraphrases/obfuscations; an adaptive attacker who knows the detector is not covered. Treat as a generalization check, not proof of security.
