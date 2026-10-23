# Blind multilingual corpus + embedding cascade

30 attacks (DE/FR/ES/BS) + 10 benign tasks, authored for this check.

| Layer | Blocked | FP | Time |
|---|---:|---:|---:|
| lexical (`agent-immunity` v2) | **4/30 = 13.3%** | 0/10 | 0.02 s |
| `gamai_guard` + bge-m3 cascade | **29/30 = 96.7%** | **0/10** | 55 s (batch + prototype cache) |

The lexical layer is English/Bosnian-specific. bge-m3 embeddings with
English/Bosnian prototypes transfer across DE/FR/ES; the one miss is a
wording edge case. The analytic guard prevents the French "explain how
prompt-injection works" false positive.

Latency is not production: Contabo was at load ~94 and bge-m3 runs on CPU.
Batch + prototype cache cut 190 s -> 55 s; per item is still ~1.4 s. For the
lab, run it as an async second layer; keep E4 Qwen3B on VastVM GPU. Prototype
vectors are cached in `~/.cache/gamai_guard/`.

Artifacts: `labs/blind_multilingual.jsonl`, `labs/eval_blind.py`,
`labs/blind_multilingual_results.json`.
