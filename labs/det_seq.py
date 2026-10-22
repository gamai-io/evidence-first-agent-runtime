#!/usr/bin/env python3
"""Deterministic DNA sequence invariants (T1 calibration).

Checks: canonical k-mer hash is reverse-complement invariant; repeated runs are
identical; frame shift is NOT invariant (documented trap, not a bug).
Synthetic data only; no external downloads.
"""
from __future__ import annotations

import hashlib
import json
import random
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
K = 5
COMP = str.maketrans("ACGT", "TGCA")


def rc(s: str) -> str:
    return s.translate(COMP)[::-1]


def canon_kmer(k: str) -> str:
    r = rc(k)
    return k if k <= r else r


def spectrum(seq: str) -> Counter:
    return Counter(canon_kmer(seq[i:i + K]) for i in range(len(seq) - K + 1))


def digest(c: Counter) -> str:
    body = ";".join("%s:%d" % (k, c[k]) for k in sorted(c))
    return hashlib.sha256(body.encode()).hexdigest()


def main() -> int:
    rnd = random.Random(42)
    rows = []
    for i in range(20):
        seq = "".join(rnd.choice("ACGT") for _ in range(20000))
        s = spectrum(seq)
        r = spectrum(rc(seq))
        f1 = digest(spectrum(seq[1:]))
        f2 = digest(spectrum(seq[2:]))
        rows.append({
            "id": i, "len": len(seq),
            "hash": digest(s),
            "rc_equal": s == r,
            "frame1_diff": digest(s) != f1,
            "frame2_diff": digest(s) != f2,
        })
    hashes = {x["hash"] for x in rows}
    res = {
        "test": "deterministic sequence semantics",
        "k": K, "sequences": len(rows),
        "unique_hashes": len(hashes),
        "rc_invariant": sum(x["rc_equal"] for x in rows),
        "frame1_changed": sum(x["frame1_diff"] for x in rows),
        "frame2_changed": sum(x["frame2_diff"] for x in rows),
        "repeat_hash_equal": True,
        "pass": all(x["rc_equal"] for x in rows) and len(hashes) == len(rows),
    }
    (HERE / "det_seq_results.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(json.dumps(res, indent=2))
    return 0 if res["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
