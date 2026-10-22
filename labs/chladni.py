#!/usr/bin/env python3
"""T3: analytic Chladni/membrane mode calibration.

No public image dataset is available, so this is a solver self-test, not a
validation of cymatics. It checks nodal-line counts and eigenfrequency ratios
against the closed-form rectangular membrane solution.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
MODES = [(1, 1), (2, 1), (1, 2), (2, 2), (3, 2), (3, 3)]
GRID = 401


def mode(n: int, m: int) -> np.ndarray:
    x = np.linspace(0.0, 1.0, GRID)
    y = np.linspace(0.0, 1.0, GRID)
    X, Y = np.meshgrid(x, y)
    return np.sin(n * math.pi * X) * np.sin(m * math.pi * Y)


def nodal_counts(z: np.ndarray) -> tuple[int, int]:
    # interior zero crossings along the two axes at the center row/column
    row = z[GRID // 2, 1:-1]
    col = z[1:-1, GRID // 2]
    vx = int(np.sum(np.sign(row[:-1]) != np.sign(row[1:])))
    vy = int(np.sum(np.sign(col[:-1]) != np.sign(col[1:])))
    return vx, vy


def main() -> int:
    rows = []
    base = math.sqrt(2.0)
    ok = True
    for n, m in MODES:
        z = mode(n, m)
        vx, vy = nodal_counts(z)
        expect_v = n - 1
        expect_h = m - 1
        freq = math.sqrt(n * n + m * m) / base
        good = (vx == expect_v and vy == expect_h)
        ok = ok and good
        rows.append({"mode": [n, m], "vertical_crossings": vx,
                     "horizontal_crossings": vy,
                     "expected": [expect_v, expect_h],
                     "freq_ratio_to_11": round(freq, 6),
                     "pass": good})
    res = {
        "test": "analytic Chladni/membrane calibration",
        "grid": GRID, "modes": len(MODES),
        "rows": rows, "pass": ok,
        "scope": "solver self-test only; no public image dataset; no cymatics claim",
    }
    (HERE / "chladni_results.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(json.dumps(res, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
