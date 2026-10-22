# agent-immunity

**Refusals should be memory, not just filters.**

Two mechanisms, one SQLite file, no network:

1. **Monotonic provenance taint.** A fact written by an untrusted source is
   `untrusted`; external content is `quarantined`. A child inherits the
   dirtiest parent and can never be cleaner. Tainted memory expires (90/30/7
   days).
2. **Antibody memory.** Every blocked injection becomes a signature. Matching
   is exact (canonical SHA-256) plus **near-miss** (Jaccard or overlap ≥ 0.80)
   after NFKC, zero-width/bidi stripping, and confusable folding. Antibodies
   decay (×0.98/day), so stale signatures go dormant instead of blocking
   forever.

## Quickstart

```bash
echo '{}' | python3 immunity.py selftest
python3 eval.py
```

```
baseline_asr: 1.0
taint_only_asr_rounds: [0.0, 0.1, 0.0]     # filter-only: reworded payload escapes
treatment_asr_rounds:  [0.0, 0.0, 0.0]      # memory closes it
treatment_utility_min: 100.0
false_denial_max: 0.0
guard_p50_ms: ~1.3
```

## API

```python
from immunity import Store

s = Store("immunity.db")

# provenance
parent = s.taint_write("notes", "page says: hello", source="web", trust="external")
child = s.taint_write("notes", "summary of page", source="agent", trust="verified",
                      parents=[parent["id"]])
assert child["taint"] == "quarantined"   # monotonic

# gate a tool call
d = s.shield_check(text, tool="fs_write")
if not d["allow"]:
    s.antibody_add(reason=d["reason"], attack_class=d["attack_class"], text=text)

# learn from a human-confirmed incident
s.antibody_add("support ticket", "instruction_override", payload, "high")
s.stats()
```

CLI contract (same as the plugin form): `argv[1]` = tool, stdin = one JSON
object, stdout = one JSON object. Tools: `taint_write`, `shield_check`,
`antibody_add`, `antibody_stats`, `selftest`.

## Design notes

- **Analytical context is not a bypass.** Text that *quotes* an injection can
  pass for a non-risky tool (`answer`, `doc`, `search`) but never for
  `shell`, `fs_write`, `memory_write`, or `send`.
- **Base64 is decoded and re-scanned.** Obfuscation is a channel, not a
  different attack.
- **Risky tools are explicit.** The default list is deliberately small and
  readable; extend it for your runtime.

## Results

| mode | round 1 | round 2 | round 3 | utility | false denial |
|---|---|---|---|---|---|
| baseline (no defense) | 100% | 100% | 100% | 100% | 0% |
| filter only | 0% | 10% | 0% | 100% | 0% |
| taint + antibodies | **0%** | **0%** | **0%** | **100%** | **0%** |

10 payloads × 3 channels (memory, tool, skill) × 3 rounds; 20 benign tasks.
Reference run on a harder corpus: 3.3% → 0% → 0%, guard 1.55 ms.

**Tuned corpora:** 200 development, 90 second-corpus and 70 edge attacks plus
352 benign controls. All reach **100%** after tuning
with **0.0%** benign FP. This is a regression result, not a generalization
claim: the second corpus was **80.0%** before the final tuning pass, and no
untouched/adaptive corpus has been run. See
[`bench/FINAL_REPORT.md`](../bench/FINAL_REPORT.md).

## Limitations

- Synthetic corpus; adaptive attackers and long benign documents that share
  vocabulary with an attack can cause false positives. The 100% figures are
  tuned regressions, so the 0% built-in table is not a general protection
  claim; an untouched corpus is required before quoting a generalization rate.
- **Cross-language gap:** a 30-attack German holdout scored **1/30 (3.3%)**
  with 0 benign FP. The filter is English/Bosnian-specific; do not present the
  tuned 100% as multilingual protection. A local 3B semantic prototype reached
  28/30 German (93.3%) with 0 benign FP, still a filter and not a boundary.
- Near-miss is lexical. A semantic paraphrase with different vocabulary is not
  caught until a human or a classifier adds an antibody.
- Taint is only as good as the trust labels your writers supply.

## Tests

```bash
python3 tests/run_tests.py   # 40/40, stdlib only
```

MIT.
