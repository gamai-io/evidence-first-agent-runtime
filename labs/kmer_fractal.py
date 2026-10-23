#!/usr/bin/env python3
"""T6: CGR box-counting on real genomes vs shuffled controls.

Exploratory. It measures k-mer/CGR occupancy, not a biological "fractal code".
A lower D than a mononucleotide-shuffled control means composition/k-mer bias;
this test does not separate biology from nucleotide composition.
"""
from __future__ import annotations

import json
import math
import random
import statistics
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ACC = {
    "SARS-CoV-2": "NC_045512.2",
    "E. coli K-12": "NC_000913.3",
    "human mtDNA": "NC_012920.1",
    "yeast chr1": "NC_001133.9",
}
MAP = {"A": (0.0, 0.0), "C": (0.0, 1.0), "G": (1.0, 1.0), "T": (1.0, 0.0)}
LIMIT = 200_000
SHUFFLES = 5


def fetch(acc: str) -> str:
    url = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
           f"?db=nuccore&id={acc}&rettype=fasta&retmode=text")
    req = urllib.request.Request(url, headers={"User-Agent": "gamai-labs/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read().decode("ascii", "replace")
    return "".join(x.strip() for x in raw.splitlines() if not x.startswith(">")).upper()


def cgr_dimension(seq: str) -> float:
    x = y = 0.5
    boxes: set[tuple[int, int]] = set()
    n = 256
    for ch in seq:
        c = MAP.get(ch)
        if c is None:
            continue
        x = (x + c[0]) / 2.0
        y = (y + c[1]) / 2.0
        boxes.add((int(x * n), int(y * n)))
    pts = [(bx / n, by / n) for bx, by in boxes]
    xs, ys = [], []
    for s in range(1, 9):
        m = 2 ** s
        b = {(int(px * m), int(py * m)) for px, py in pts}
        xs.append(math.log(1.0 / m))
        ys.append(math.log(len(b)))
    mx, my = statistics.mean(xs), statistics.mean(ys)
    slope = sum((a - mx) * (b - my) for a, b in zip(xs, ys)) / sum((a - mx) ** 2 for a in xs)
    return -slope


def main() -> int:
    out = {"test": "CGR box-counting, genome vs mononucleotide shuffle",
           "limit_bp": LIMIT, "shuffles": SHUFFLES, "rows": []}
    rnd = random.Random(7)
    for name, acc in ACC.items():
        try:
            seq = fetch(acc)[:LIMIT]
            if len(seq) < 1000:
                raise RuntimeError("too short: %d" % len(seq))
            real = cgr_dimension(seq)
            nulls = []
            chars = list(seq)
            for _ in range(SHUFFLES):
                rnd.shuffle(chars)
                nulls.append(cgr_dimension("".join(chars)))
            mu, sd = statistics.mean(nulls), statistics.pstdev(nulls)
            z = (real - mu) / sd if sd else 0.0
            out["rows"].append({"name": name, "acc": acc, "bp_used": len(seq),
                                "D_real": round(real, 4), "D_shuffle_mean": round(mu, 4),
                                "shuffle_sd": round(sd, 4), "delta": round(real - mu, 4), "z": round(z, 2)})
            print(name, out["rows"][-1], flush=True)
        except Exception as exc:
            out["rows"].append({"name": name, "acc": acc, "error": str(exc)})
            print(name, "ERROR", exc, flush=True)
    (HERE / "kmer_fractal_results.json").write_text(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
