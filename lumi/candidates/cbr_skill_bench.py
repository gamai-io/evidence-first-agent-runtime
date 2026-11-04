#!/usr/bin/env python3
"""Skill matcher + CBR retrieval bench (portable, synthetic, stdlib only).

Measures a token-set/BM25-lite skill router over 500 skills and a case-based
reasoning (CBR) store over 1000 cases, with latency and domain accuracy.
"""
import argparse, json, math, random, re, sqlite3, tempfile, time

DOMAINS = ["sql", "prodaja", "pravo", "marketing", "logistika", "finansije", "code", "hr", "it", "podrska"]

def toks(t): return re.findall(r"[a-z0-9]+", str(t or "").lower())

def make_skills(n=500):
    out = []
    for i in range(n):
        d = DOMAINS[i % len(DOMAINS)]
        out.append({"id": "skill-%03d" % i, "name": "gama-%s-%d" % (d, i),
                    "desc": "pomoc za %s zadatke, korak %d, domena %s" % (d, i % 7, d)})
    return out

class Matcher:
    def __init__(self, items):
        self.items = items
        self.df = {}; self.docs = []
        for it in items:
            tk = set(toks(it["name"] + " " + it["desc"]))
            self.docs.append(tk)
            for x in tk: self.df[x] = self.df.get(x, 0) + 1
        self.N = len(items)
    def score(self, q, i):
        qt = toks(q); s = 0.0
        for x in set(qt):
            if x in self.docs[i]:
                idf = math.log(1 + (self.N - self.df[x] + 0.5) / (self.df[x] + 0.5))
                s += idf * (1 + qt.count(x) * 0.25)
        return s
    def best(self, q, k=1):
        return sorted(range(self.N), key=lambda i: -self.score(q, i))[:k]

def jac(a, b):
    A, B = set(a), set(b)
    return len(A & B) / max(1, len(A | B))

def make_cases(n=1000):
    rows = []
    for i in range(n):
        d = DOMAINS[i % len(DOMAINS)]
        rows.append({"goal": "rijesi %s slucaj %d" % (d, i), "steps": "query_%s;validate;reply" % d})
    return rows

def bench(skills, cases, nq=200):
    m = Matcher(skills); rnd = random.Random(42)
    qs = [("treba mi %s pomoc" % DOMAINS[rnd.randrange(len(DOMAINS))]) for i in range(nq)]
    t0 = time.perf_counter(); hit1 = 0
    for q in qs:
        best = m.best(q, 1)[0]
        if DOMAINS[best % len(DOMAINS)] == toks(q)[2]:
            hit1 += 1
    match_ms = (time.perf_counter() - t0) * 1000
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE cases(id INTEGER PRIMARY KEY, goal TEXT, steps TEXT)")
    db.executemany("INSERT INTO cases(goal,steps) VALUES(?,?)", [(c["goal"], c["steps"]) for c in cases])
    db.commit()
    t0 = time.perf_counter(); hit3 = 0
    for i in range(nq):
        d = DOMAINS[i % len(DOMAINS)]
        q = "rijesi %s slucaj %d" % (d, i)
        qt = set(toks(q)); scored = []
        for cid, goal, steps in db.execute("SELECT id,goal,steps FROM cases"):
            scored.append((jac(qt, toks(goal + " " + steps)), cid))
        top = sorted(scored, reverse=True)[:3]
        if any(DOMAINS[(cid - 1) % len(DOMAINS)] == d for _, cid in top):
            hit3 += 1
    cbr_ms = (time.perf_counter() - t0) * 1000
    return {"skills": len(skills), "queries": nq, "skill_acc_at_1": round(hit1/nq, 3),
            "skill_ms_total": round(match_ms, 2), "skill_ms_per_query": round(match_ms/nq, 3),
            "cases": len(cases), "cbr_hit_at_3": round(hit3/nq, 3),
            "cbr_ms_total": round(cbr_ms, 2), "cbr_ms_per_query": round(cbr_ms/nq, 3)}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--skills", type=int, default=500)
    ap.add_argument("--cases", type=int, default=1000)
    ap.add_argument("--json-out")
    a = ap.parse_args()
    res = bench(make_skills(a.skills), make_cases(a.cases))
    ok = res["skill_acc_at_1"] >= 0.9 and res["cbr_hit_at_3"] >= 0.9
    if a.selftest:
        print("SELFTEST", "PASS" if ok else "FAIL", json.dumps(res, ensure_ascii=False))
        raise SystemExit(0 if ok else 1)
    s = json.dumps(res, ensure_ascii=False, indent=2); print(s)
    if a.json_out: open(a.json_out, "w", encoding="utf-8").write(s+"\n")

if __name__ == "__main__": main()
