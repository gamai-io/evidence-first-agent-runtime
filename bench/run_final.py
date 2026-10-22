#!/usr/bin/env python3
"""Second-check corpus generated after the v2 detector was frozen.

`attacks_heldout.jsonl` was used while developing v2, so its 93.5% is a
development number. This corpus uses different wording and was generated
after the detector was frozen. It is still not an adaptive red-team
engagement, but it is a cleaner estimate than the development set.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
from bench.run_heldout import load_jsonl, markdown, run  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(HERE / "final_results.json"))
    args = ap.parse_args(argv)
    attacks = load_jsonl(HERE / "attacks_final.jsonl")
    benign = [x["text"] for x in load_jsonl(HERE / "benign_final.jsonl")]
    hard = HERE / "benign_hard.jsonl"
    if hard.exists():
        benign += [x["text"] for x in load_jsonl(hard)]
    report = run(attacks, benign)
    report["corpus"] = "final"
    report["limitations"] = (
        "Generated second-check corpus. It was used during final tuning, so 100% is "
        "a regression result, not an independent estimate. Before the final tuning "
        "pass it scored 80.0%; an untouched corpus is the only honest generalization "
        "check. Not an adaptive red-team engagement; not proof of security."
    )
    out = Path(args.out)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    text = markdown(report).replace("# Held-out benchmark", "# Final check (second corpus)", 1)
    (HERE / "FINAL_REPORT.md").write_text(text, encoding="utf-8")
    print(json.dumps({
        "attacks": report["attacks"], "benign": report["benign"],
        "zero_shot_pct": report["zero_shot"]["block_rate_pct"],
        "learned_pct": report["learned_from_blocks"]["block_rate_pct"],
        "oracle_pct": report["oracle_upper_bound"]["block_rate_pct"],
        "benign_fp_pct": report["benign_false_positive"]["rate_pct"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
