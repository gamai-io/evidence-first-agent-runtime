#!/usr/bin/env python3
"""Run the held-out attack corpus against agent-immunity.

Measurements:
  1. zero-shot      pattern shield, no learned antibodies
  2. learned        antibodies learned only from attacks that were blocked
  3. oracle         antibodies added for every attack (upper bound, not deployable)
  4. benign         false positives on 100 ordinary tasks

The v1 corpus was originally held out. The v2 lexicon was developed with this
corpus in view, so these are **development-set** numbers, not an independent
estimate. `bench/run_final.py` runs a corpus generated after the v2 detector was
frozen. Neither corpus models an adaptive attacker.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from gamai_trust import immunity  # noqa: E402

HERE = Path(__file__).resolve().parent


def load_jsonl(path: Path) -> list[dict]:
    items = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def tool_for(cls: str) -> str:
    if cls == "memory_persistence":
        return "memory_write"
    if cls == "tool_injection":
        return "shell"
    return "answer"


def fresh_store() -> "immunity.Store":
    path = tempfile.mktemp(prefix="heldout-", suffix=".db")
    return immunity.Store(path)


def blocked(store, text: str, cls: str) -> tuple[bool, float]:
    t0 = time.perf_counter()
    decision = store.shield_check(text, tool=tool_for(cls))
    ms = (time.perf_counter() - t0) * 1000.0
    return (not bool(decision.get("allow"))), ms


def by_class() -> dict:
    return {}


def run(attacks: list[dict], benign: list[str]) -> dict:
    # 1) zero-shot
    zs = fresh_store()
    zs_blocked = 0
    zs_lat: list[float] = []
    zs_classes: dict[str, dict] = {}
    for item in attacks:
        hit, ms = blocked(zs, item["text"], item["class"])
        zs_blocked += int(hit)
        zs_lat.append(ms)
        c = zs_classes.setdefault(item["class"], {"n": 0, "blocked": 0})
        c["n"] += 1
        c["blocked"] += int(hit)

    # 2) learned from blocks only
    learned = fresh_store()
    learned_blocked = 0
    learnable = 0
    learnable_hits = 0
    learned_lat: list[float] = []
    learned_classes: dict[str, dict] = {}
    for item in attacks:
        hit, _ = blocked(learned, item["text"], item["class"])
        if hit:
            learnable += 1
            learned.antibody_add("heldout", item["class"], item["text"], "high")
        vhit, ms = blocked(learned, item["variant"], item["class"])
        learned_blocked += int(vhit)
        if hit and vhit:
            learnable_hits += 1
        learned_lat.append(ms)
        c = learned_classes.setdefault(item["class"], {"n": 0, "blocked": 0})
        c["n"] += 1
        c["blocked"] += int(vhit)

    # 3) oracle: antibody for every attack (upper bound of the memory mechanism)
    oracle = fresh_store()
    oracle_blocked = 0
    oracle_lat: list[float] = []
    oracle_classes: dict[str, dict] = {}
    for item in attacks:
        oracle.antibody_add("heldout-oracle", item["class"], item["text"], "high")
        vhit, ms = blocked(oracle, item["variant"], item["class"])
        oracle_blocked += int(vhit)
        oracle_lat.append(ms)
        c = oracle_classes.setdefault(item["class"], {"n": 0, "blocked": 0})
        c["n"] += 1
        c["blocked"] += int(vhit)

    # 4) benign false positives (zero-shot and after learned antibodies)
    benign_hits = 0
    benign_lat: list[float] = []
    for text in benign:
        hit, ms = blocked(zs, text, "benign")
        benign_hits += int(hit)
        benign_lat.append(ms)
    benign_after_hits = 0
    for text in benign:
        hit, _ = blocked(learned, text, "benign")
        benign_after_hits += int(hit)

    def pct(n: int, d: int) -> float:
        return round(100.0 * n / d, 2) if d else 0.0

    def lat(values: list[float]) -> dict:
        if not values:
            return {"p50": 0.0, "p95": 0.0}
        s = sorted(values)
        return {
            "p50": round(statistics.median(s), 2),
            "p95": round(s[min(len(s) - 1, int(len(s) * 0.95))], 2),
        }

    return {
        "ok": True,
        "attacks": len(attacks),
        "benign": len(benign),
        "zero_shot": {
            "blocked": zs_blocked,
            "block_rate_pct": pct(zs_blocked, len(attacks)),
            "by_class": zs_classes,
            "latency_ms": lat(zs_lat),
        },
        "learned_from_blocks": {
            "blocked": learned_blocked,
            "block_rate_pct": pct(learned_blocked, len(attacks)),
            "learnable": learnable,
            "learnable_variant_blocked": learnable_hits,
            "learnable_variant_rate_pct": pct(learnable_hits, learnable),
            "by_class": learned_classes,
            "latency_ms": lat(learned_lat),
        },
        "oracle_upper_bound": {
            "blocked": oracle_blocked,
            "block_rate_pct": pct(oracle_blocked, len(attacks)),
            "by_class": oracle_classes,
            "latency_ms": lat(oracle_lat),
        },
        "benign_false_positive": {
            "blocked": benign_hits,
            "rate_pct": pct(benign_hits, len(benign)),
            "latency_ms": lat(benign_lat),
            "after_learning_blocked": benign_after_hits,
            "after_learning_rate_pct": pct(benign_after_hits, len(benign)),
        },
        "limitations": (
            "The v1 corpus was originally held out, but v2 was developed and "
            "tuned against it. 100% is a development/regression result, not an "
            "independent estimate. An untouched corpus is the only honest "
            "generalization check; an adaptive attacker is not covered."
        ),
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def markdown(report: dict) -> str:
    corpus = report.get("corpus", "development")
    if corpus == "final":
        title = "# Final check (second corpus)"
    elif corpus == "edge":
        title = "# Edge regression corpus"
    else:
        title = "# Development corpus (v1 held-out, now used for v2)"
    lines = [
        title,
        "",
        "Generated corpus: **%d attacks**, **%d benign tasks**. "
        "Not an independent red-team engagement; see limitations below." % (
            report["attacks"], report["benign"]),
        "",
    ]
    if corpus == "development":
        lines += [
            "> This corpus was held out for v1. The v2 lexicon was developed with it "
            "in view, so **100% is a development number**. The second check is in "
            "[FINAL_REPORT.md](FINAL_REPORT.md).",
            "",
        ]
    lines += [
        "| Mode | Blocked | Rate | p50 | p95 |",
        "|---|---:|---:|---:|---:|",
    ]
    for key, label in (
        ("zero_shot", "zero-shot (patterns + v2 lexicon)"),
        ("learned_from_blocks", "learned from blocked attacks"),
        ("oracle_upper_bound", "oracle upper bound (all labels)"),
    ):
        x = report[key]
        lines.append("| %s | %d/%d | %.2f%% | %.2f ms | %.2f ms |" % (
            label, x["blocked"], report["attacks"], x["block_rate_pct"],
            x["latency_ms"]["p50"], x["latency_ms"]["p95"]))
    b = report["benign_false_positive"]
    lines.append("| benign false positives | %d/%d | %.2f%% | %.2f ms | %.2f ms |" % (
        b["blocked"], report["benign"], b["rate_pct"],
        b["latency_ms"]["p50"], b["latency_ms"]["p95"]))
    lf = report["learned_from_blocks"]
    lines += ["", "Learned antibodies generalize to the variant for "
              "**%d/%d** attacks that were blocked at least once (%.1f%%)." % (
                  lf["learnable_variant_blocked"], lf["learnable"],
                  lf["learnable_variant_rate_pct"]), ""]
    lines += ["## By class (zero-shot)", "",
              "| Class | n | blocked | rate |", "|---|---:|---:|---:|"]
    for cls, v in sorted(report["zero_shot"]["by_class"].items()):
        rate = 100.0 * v["blocked"] / v["n"] if v["n"] else 0.0
        lines.append("| %s | %d | %d | %.1f%% |" % (cls, v["n"], v["blocked"], rate))
    lines += ["", "## Limitations", "", report["limitations"], ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="limit attacks (0 = all)")
    ap.add_argument("--out", default=str(HERE / "heldout_results.json"))
    args = ap.parse_args(argv)

    attacks = load_jsonl(HERE / "attacks_heldout.jsonl")
    benign = [x["text"] for x in load_jsonl(HERE / "benign_heldout.jsonl")]
    hard_path = HERE / "benign_hard.jsonl"
    if hard_path.exists():
        benign += [x["text"] for x in load_jsonl(hard_path)]
    if args.limit and args.limit > 0:
        attacks = attacks[:args.limit]
    report = run(attacks, benign)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if out.name == "heldout_results.json":
        (HERE / "HELDOUT_REPORT.md").write_text(markdown(report), encoding="utf-8")
    print(json.dumps({
        "attacks": report["attacks"],
        "zero_shot_pct": report["zero_shot"]["block_rate_pct"],
        "learned_pct": report["learned_from_blocks"]["block_rate_pct"],
        "oracle_pct": report["oracle_upper_bound"]["block_rate_pct"],
        "benign_fp_pct": report["benign_false_positive"]["rate_pct"],
        "out": str(out),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
