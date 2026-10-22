#!/usr/bin/env python3
"""T2: canonical AST hash vs ECC integrity under structured mutations.

No execution of mutants. Two independent claims:
  A) canonical AST hash ignores formatting/comments (M5/M6) and detects
     constant/control-flow/dead-code changes (M2/M4). Rename (M1) is
     semantics-preserving but changes the AST; report it honestly.
  B) repetition-3 + CRC32 detects/corrects a bounded number of byte errors
     and detects truncation.
"""
from __future__ import annotations

import ast
import hashlib
import json
import random
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
N = 40
CLASSES = ("rename", "constant", "control", "dead", "format", "comment")


def base(i: int) -> str:
    return "def f%d(x):\n    return x + %d\n" % (i, i)


def mutate(src: str, i: int, cls: str) -> str:
    if cls == "rename":
        return src.replace("f%d" % i, "g%d" % i).replace("(x)", "(value)")
    if cls == "constant":
        return src.replace("+ %d" % i, "+ %d" % (i + 100))
    if cls == "control":
        return src.replace("return x + %d" % i,
                           "if x > 0:\n        return x + %d\n    return x - %d" % (i, i))
    if cls == "dead":
        return src.replace("return x + %d" % i,
                           "if False:\n        return -1\n    return x + %d" % i)
    if cls == "format":
        return src.replace("\n", "\n\n    ").replace("    return", "        return")
    if cls == "comment":
        return "# ünïcode comment Δ\n" + src + "# trailing comment\n"
    raise ValueError(cls)


def digest(src: str) -> str:
    tree = ast.parse(src)
    body = ast.dump(tree, annotate_fields=True, include_attributes=False)
    return hashlib.sha256(body.encode()).hexdigest()


def ecc_encode(data: bytes) -> bytes:
    out = bytearray()
    for b in data:
        out += bytes([b, b, b])
    out += zlib.crc32(data).to_bytes(4, "big")
    return bytes(out)


def ecc_decode(code: bytes) -> tuple[bytes, bool, bool]:
    payload = code[:-4]
    crc = code[-4:]
    if len(payload) % 3:
        return b"", False, False
    out = bytearray()
    for i in range(0, len(payload), 3):
        a, b, c = payload[i:i + 3]
        out.append(a if (a == b or a == c) else b)
    ok = zlib.crc32(bytes(out)).to_bytes(4, "big") == crc
    return bytes(out), ok, ok


def flips(code: bytes, rnd: random.Random, n: int) -> bytes:
    b = bytearray(code)
    for _ in range(n):
        k = rnd.randrange(len(b) - 4)
        b[k] ^= 1 << rnd.randrange(8)
    return bytes(b)


def main() -> int:
    rnd = random.Random(7)
    matrix = {c: {"n": 0, "detected": 0, "same": 0} for c in CLASSES}
    for i in range(N):
        base_src = base(i)
        h0 = digest(base_src)
        for cls in CLASSES:
            m = mutate(base_src, i, cls)
            same = digest(m) == h0
            matrix[cls]["n"] += 1
            matrix[cls]["same"] += int(same)
            matrix[cls]["detected"] += int(not same)

    for cls in CLASSES:
        row = matrix[cls]
        row["same_pct"] = round(100.0 * row["same"] / row["n"], 2)
        row["detected_pct"] = round(100.0 * row["detected"] / row["n"], 2)

    data = b"GAMA-ECC-TEST-" + bytes(range(32))
    code = ecc_encode(data)
    errs = []
    for n in (0, 1, 2, 3):
        ok = 0
        corrected = 0
        false_accept = 0
        for _ in range(200):
            bad = flips(code, rnd, n)
            dec, valid, _ = ecc_decode(bad)
            if valid and dec == data:
                ok += 1
            elif valid and dec != data:
                false_accept += 1
            elif not valid:
                corrected += 1
        errs.append({"flips": n, "accepted": ok, "detected": corrected,
                     "false_accept": false_accept})

    trunc = ecc_decode(code[:-3])
    res = {
        "test": "ECC + canonical AST hash",
        "programs": N,
        "ast": matrix,
        "ecc": {"bytes": len(data), "code_bytes": len(code),
                "trials_per_flip_count": 200, "results": errs,
                "truncation_detected": not trunc[2]},
        "pass": (
            matrix["constant"]["detected"] == N
            and matrix["control"]["detected"] == N
            and matrix["dead"]["detected"] == N
            and matrix["format"]["same"] == N
            and matrix["comment"]["same"] == N
            and all(x["false_accept"] == 0 for x in errs)
            and not trunc[2]
        ),
    }
    (HERE / "ecc_hash_results.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(json.dumps(res, indent=2))
    return 0 if res["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
