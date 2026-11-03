#!/usr/bin/env python3
"""Retrieval eval: BM25 vs dense vs RRF (portable, stdlib-only selftest).

Deterministic synthetic corpus (no private data). Reports recall@1/@5 and nDCG@5.
Dense backend is optional via EMBED_URL (OpenAI-compatible /v1/embeddings).

  python3 retrieval_eval.py --selftest
  EMBED_URL=http://127.0.0.1:8064/v1/embeddings python3 retrieval_eval.py --docs 200 --queries 40
"""
import argparse, json, math, os, re, time, urllib.request

def toks(t): return re.findall(r"[a-z0-9]+", (t or "").lower())

class BM25:
    def __init__(self, docs, k1=1.5, b=0.75):
        self.docs = docs; self.k1, self.b = k1, b
        self.tf = [ {} for _ in docs ]; self.dl = []
        df = {}
        for i, d in enumerate(docs):
            w = toks(d); self.dl.append(len(w))
            for x in w: self.tf[i][x] = self.tf[i].get(x, 0) + 1
            for x in set(w): df[x] = df.get(x, 0) + 1
        self.N = len(docs); self.avgdl = sum(self.dl)/max(1, self.N); self.df = df
    def score(self, q, i):
        s = 0.0
        for x in toks(q):
            if x not in self.tf[i]: continue
            idf = math.log(1 + (self.N - self.df.get(x, 0) + 0.5) / (self.df.get(x, 0) + 0.5))
            f = self.tf[i][x]; dl = self.dl[i] or 1
            s += idf * (f*(self.k1+1)) / (f + self.k1*(1 - self.b + self.b*dl/self.avgdl))
        return s
    def search(self, q, k=5):
        return sorted(range(self.N), key=lambda i: -self.score(q, i))[:k]

def embed(texts, url, model):
    out = []
    for i in range(0, len(texts), 16):
        body = json.dumps({"model": model, "input": texts[i:i+16]}).encode()
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=300) as r:
            out.extend([x["embedding"] for x in json.loads(r.read())["data"]])
    return out

def cos(a, b): return sum(x*y for x, y in zip(a, b))

def rrf(ranks, k=60):
    sc = {}
    for r in ranks:
        for pos, i in enumerate(r):
            sc[i] = sc.get(i, 0.0) + 1.0/(k + pos + 1)
    return [i for i, _ in sorted(sc.items(), key=lambda x: -x[1])]

def metrics(results, truth, k=5):
    r1 = sum(1 for a, t in zip(results, truth) if a and t in a[:1]) / len(truth)
    r5 = sum(1 for a, t in zip(results, truth) if t in a[:k]) / len(truth)
    nd = 0.0
    for a, t in zip(results, truth):
        for pos, i in enumerate(a[:k]):
            if i == t: nd += 1.0/math.log2(pos+2); break
    return {"recall_at_1": round(r1, 3), "recall_at_5": round(r5, 3), "ndcg_at_5": round(nd/len(truth), 3)}

def corpus(n_docs, n_queries):
    docs = [f"document {i} about topic {i % 20} with filler text" for i in range(n_docs)]
    queries = [f"topic {i % 20}" for i in range(n_queries)]
    truth = [i % 20 for i in range(n_queries)]
    # ground truth = a doc index for that topic
    gt_idx = [truth[i] % n_docs for i in range(n_queries)]
    return docs, queries, gt_idx

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--docs", type=int, default=200)
    ap.add_argument("--queries", type=int, default=40)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--embed-url", default=os.environ.get("EMBED_URL"))
    ap.add_argument("--embed-model", default=os.environ.get("EMBED_MODEL", "bge-m3"))
    ap.add_argument("--json-out")
    a = ap.parse_args()
    docs, queries, gt = corpus(a.docs, a.queries)
    bm = BM25(docs)
    t0 = time.perf_counter(); bm_res = [bm.search(q, a.k) for q in queries]; bm_ms = (time.perf_counter()-t0)*1000
    out = {"docs": a.docs, "queries": a.queries, "bm25": metrics(bm_res, gt, a.k), "bm25_ms_total": round(bm_ms, 2)}
    if a.embed_url:
        dv = embed(docs, a.embed_url, a.embed_model); qv = embed(queries, a.embed_url, a.embed_model)
        t0 = time.perf_counter()
        dense = [sorted(range(len(docs)), key=lambda i: -cos(qv[j], dv[i]))[:a.k] for j in range(len(queries))]
        dense_ms = (time.perf_counter()-t0)*1000
        fused = [rrf([bm_res[j], dense[j]])[:a.k] for j in range(len(queries))]
        out["dense"] = metrics(dense, gt, a.k); out["dense_ms_total"] = round(dense_ms, 2)
        out["rrf"] = metrics(fused, gt, a.k); out["backend"] = "http"; out["embed_model"] = a.embed_model
    if a.selftest:
        ok = out["bm25"]["recall_at_5"] >= 0.9
        print("SELFTEST", "PASS" if ok else "FAIL", json.dumps(out, ensure_ascii=False))
        raise SystemExit(0 if ok else 1)
    s = json.dumps(out, ensure_ascii=False, indent=2); print(s)
    if a.json_out: open(a.json_out, "w", encoding="utf-8").write(s+"\n")

if __name__ == "__main__": main()
