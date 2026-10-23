#!/usr/bin/env python3
"""Evaluate lexical vs batch embedding cascade on a blind multilingual corpus."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from gamai_guard.text import Cascade  # noqa: E402

HERE = Path(__file__).resolve().parent


def main() -> int:
    rows = [json.loads(x) for x in (HERE / "blind_multilingual.jsonl").read_text(encoding="utf-8").splitlines() if x]
    attacks = [r for r in rows if r["class"] != "benign"]
    benign = [r for r in rows if r["class"] == "benign"]
    out = {"lexical": {"attacks": len(attacks), "blocked": 0, "fp": 0},
           "embedding": {"model": None, "attacks": len(attacks), "blocked": 0, "fp": 0}}
    t0 = time.perf_counter()
    lex = Cascade(None)
    for r in attacks:
        if not lex.check(r["text"])["allow"]:
            out["lexical"]["blocked"] += 1
    for r in benign:
        if not lex.check(r["text"])["allow"]:
            out["lexical"]["fp"] += 1
    out["lexical"]["elapsed_s"] = round(time.perf_counter() - t0, 2)
    try:
        t1 = time.perf_counter()
        emb = Cascade("http://127.0.0.1:11434/api/embed", "bge-m3", 0.15)
        a = emb.check_many([r["text"] for r in attacks])
        b = emb.check_many([r["text"] for r in benign])
        out["embedding"]["model"] = "bge-m3"
        out["embedding"]["blocked"] = sum(1 for x in a if not x["allow"])
        out["embedding"]["fp"] = sum(1 for x in b if not x["allow"])
        out["embedding"]["elapsed_s"] = round(time.perf_counter() - t1, 2)
        out["embedding"]["fp_items"] = [r["text"] for r, x in zip(benign, b) if not x["allow"]]
        out["embedding"]["miss_items"] = [r["text"] for r, x in zip(attacks, a) if x["allow"]]
    except Exception as exc:
        out["embedding"]["error"] = str(exc)
    out["lexical"]["rate_pct"] = round(100.0 * out["lexical"]["blocked"] / len(attacks), 2)
    out["embedding"]["rate_pct"] = round(100.0 * out["embedding"]["blocked"] / len(attacks), 2) if out["embedding"]["model"] else None
    (HERE / "blind_multilingual_results.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
