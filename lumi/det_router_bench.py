#!/usr/bin/env python3
"""Deterministic pre-LLM router bench (stdlib only, offline).

Measures the deterministic layers that must answer/block before any model call:
  - risk gate (T1 catastrophic, T2 high) with adjacency fix
  - decimal money math (ROUND_HALF_UP)
  - tool-call JSON recovery
Run: python3 det_router_bench.py --n 10000
Selftest: python3 det_router_bench.py --selftest
"""
import argparse, json, re, time
from decimal import Decimal, ROUND_HALF_UP

T1 = [r"\brm\s+-rf\s+[/~*]", r"\bmkfs\b", r"\bdd\s+if=.*of=/dev/", r"\bdrop\s+(table|database)\b",
      r"\btruncate\s+table\b", r"\bshutdown\b", r"\breboot\b", r"\bobrisi\s+(sve|bazu|disk)\b", r"\bizbrisi\s+bazu\b"]
T2 = [r"\bobrisi\s+(fajl|folder|log)\b", r"\bobrisi\s+/var\b", r"\bobrisi\s+.*\b(log|fajl|folder)\b",
      r"\bizbrisi\s+.*\b(log|fajl|folder)\b", r"\bdelete\s+file\b", r"\bchmod\s+777\b", r"\bchown\s+-R\b",
      r"\bkillall\b", r"\bpkill\s+-9\b"]
T1C = [re.compile(p) for p in T1]
T2C = [re.compile(p) for p in T2]

def norm(t): return re.sub(r"\s+", " ", (t or "").lower().strip())

def risk(text):
    t = norm(text)
    for p in T1C:
        if p.search(t): return 0.9, "T1"
    for p in T2C:
        if p.search(t): return 0.7, "T2"
    return 0.0, "ok"

def pct(t):
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*%\s*(?:od|of)\s*(\d+(?:[.,]\d+)?)", t, re.I)
    if not m: return None
    p = Decimal(m.group(1).replace(",", ".")); x = Decimal(m.group(2).replace(",", "."))
    return (p / Decimal(100) * x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def recover_args(txt):
    # pull the first balanced JSON object out of noisy model output
    s = txt.find("{")
    while s != -1:
        depth = 0
        for i in range(s, len(txt)):
            if txt[i] == "{": depth += 1
            elif txt[i] == "}":
                depth -= 1
                if depth == 0:
                    try: return json.loads(txt[s:i+1])
                    except Exception: break
        s = txt.find("{", s + 1)
    return None

SAMPLES = ["zdravo", "2+2", "koliko ima kupaca", "napravi ponudu", "rm -rf /", "obrisi /var/log sve",
           "drop table kupci", "17% od 1450", "prebaci na podrum", "prognoza za Sarajevo"]

def run(n):
    t0 = time.perf_counter()
    blocked = 0
    for i in range(n):
        r, tier = risk(SAMPLES[i % len(SAMPLES)])
        blocked += 1 if r >= 0.7 else 0
    risk_us = (time.perf_counter() - t0) / n * 1e6

    t0 = time.perf_counter(); val = None
    for i in range(n):
        val = pct("17% od 1450")
    math_us = (time.perf_counter() - t0) / n * 1e6

    noisy = 'texto antes {"name": "sql", "arguments": {"query": "SELECT 1"}} fin'
    t0 = time.perf_counter(); okargs = 0
    for i in range(n):
        okargs += 1 if recover_args(noisy) else 0
    json_us = (time.perf_counter() - t0) / n * 1e6

    return {"n": n, "risk_us_per_call": round(risk_us, 3), "math_us_per_call": round(math_us, 3),
            "json_recover_us_per_call": round(json_us, 3), "blocked_in_sample": blocked,
            "money_example": str(val)}

def selftest():
    checks = []
    checks.append(("T1 rm -rf", risk("rm -rf /")[0] == 0.9))
    checks.append(("T1 drop table", risk("drop table kupci")[0] == 0.9))
    checks.append(("T2 var/log adjacency", risk("obrisi /var/log sve")[0] == 0.7))
    checks.append(("legit low risk", risk("napravi ponudu za ALFA")[0] == 0.0))
    checks.append(("decimal 17% 1450", str(pct("17% od 1450")) == "246.50"))
    checks.append(("json recover", recover_args('xx {"a":1} yy') == {"a": 1}))
    bad = [c for c, ok in checks if not ok]
    print("SELFTEST", "PASS" if not bad else "FAIL", "checks=%d/%d" % (len(checks) - len(bad), len(checks)))
    if bad: print("failed:", bad)
    return 0 if not bad else 1

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=10000)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--json-out")
    a = ap.parse_args()
    if a.selftest: raise SystemExit(selftest())
    res = run(a.n)
    out = json.dumps(res, ensure_ascii=False)
    print(out)
    if a.json_out: open(a.json_out, "w", encoding="utf-8").write(out + "\n")
