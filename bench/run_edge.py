#!/usr/bin/env python3
"""Edge regression corpus (70 attacks, 47 benign + 54 hard negatives).

Like the other corpora, this was used during tuning. It is a regression
suite, not an independent estimate.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from bench.run_heldout import load_jsonl, markdown, run  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(HERE / "edge_results.json"))
    args = ap.parse_args(argv)
    attacks = load_jsonl(HERE / "attacks_edge.jsonl")
    benign = [x["text"] for x in load_jsonl(HERE / "benign_edge.jsonl")]
    hard = HERE / "benign_hard.jsonl"
    if hard.exists():
        benign += [x["text"] for x in load_jsonl(hard)]
    report = run(attacks, benign)
    report["corpus"] = "edge"
    report["limitations"] = (
        "Edge regression corpus. It was used during tuning, so 100% is a "
        "regression result, not an independent estimate. Adaptive attackers "
        "are not covered."
    )
    out = Path(args.out)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (HERE / "EDGE_REPORT.md").write_text(markdown(report), encoding="utf-8")
    print(json.dumps({"attacks": report["attacks"], "benign": report["benign"],
                      "zero_shot_pct": report["zero_shot"]["block_rate_pct"],
                      "benign_fp_pct": report["benign_false_positive"]["rate_pct"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
