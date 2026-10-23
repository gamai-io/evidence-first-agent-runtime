#!/usr/bin/env python3
"""T5: I Ching 64 hexagrams vs 64 codons, as a negative control.

Fu Xi binary order (0..63) is mapped to 6-bit vectors; codons are mapped to
6 bits via A=00,C=01,G=10,T=11. Compare the two 64x64 Hamming distance matrices
with a Mantel test (10k permutations). Equal counts are not evidence of shared
structure.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
N = 64
PERM = 10000
BASES = {"A": 0, "C": 1, "G": 2, "T": 3}


def bits6(n: int) -> np.ndarray:
    return np.array([(n >> i) & 1 for i in range(5, -1, -1)], dtype=np.int8)


def codon_bits(c: str) -> np.ndarray:
    out = []
    for b in c:
        v = BASES[b]
        out += [(v >> 1) & 1, v & 1]
    return np.array(out, dtype=np.int8)


def hamming_matrix(vectors: list[np.ndarray]) -> np.ndarray:
    m = np.zeros((len(vectors), len(vectors)), dtype=np.int16)
    for i in range(len(vectors)):
        for j in range(i + 1, len(vectors)):
            d = int(np.sum(vectors[i] != vectors[j]))
            m[i, j] = m[j, i] = d
    return m


def mantel(a: np.ndarray, b: np.ndarray, rnd: random.Random, perms: int) -> tuple[float, float]:
    iu = np.triu_indices(len(a), 1)
    x, y = a[iu].astype(float), b[iu].astype(float)
    r = float(np.corrcoef(x, y)[0, 1])
    labels = list(range(len(b)))
    hits = 0
    for _ in range(perms):
        rnd.shuffle(labels)
        perm = np.array(labels)
        yp = b[np.ix_(perm, perm)][iu].astype(float)
        rp = float(np.corrcoef(x, yp)[0, 1])
        if rp >= r:
            hits += 1
    return r, (hits + 1) / (perms + 1)


def main() -> int:
    hexv = [bits6(i) for i in range(N)]
    codons = [a + b + c for a in BASES for b in BASES for c in BASES]
    codv = [codon_bits(c) for c in codons]
    dh, dc = hamming_matrix(hexv), hamming_matrix(codv)
    rnd = random.Random(7)
    r, p = mantel(dh, dc, rnd, PERM)
    res = {
        "test": "I Ching/Fu Xi 64 vs 64 codons",
        "pairs": N, "permutations": PERM,
        "mantel_r": round(r, 6), "mantel_p": round(p, 6),
        "verdict": ("tautology: both sides are the same 6-bit hypercube; "
                    "r=1 is constructed by the bit mapping, not biological evidence"),
        "evidence_for_connection": False,
        "negative_control_ok": True,
        "limits": "Equal counts (64=2^6 vs 4^3) and a distance-preserving 6-bit mapping make this test non-identifiable",
    }
    (HERE / "iching_codons_results.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
