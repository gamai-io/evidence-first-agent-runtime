#!/usr/bin/env python3
"""Chunking + rerank bench (portable, synthetic, no private data).

Compares: (A) whole-doc embedding, (B) chunk embeddings max-pool, (C) chunks + lexical rerank.
Embeddings: OpenAI-compatible /v1/embeddings (EMBED_URL) or offline toy embedder (--selftest).
"""
import argparse, hashlib, json, math, os, random, time, urllib.request

DIM = 64

def http_embed(texts, url, model):
    out = []
    for i in range(0, len(texts), 16):
        body = json.dumps({"model": model, "input": texts[i:i+16]}).encode()
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=300) as r:
            out.extend([x["embedding"] for x in json.loads(r.read())["data"]])
    return out

def toy_embed(texts):
    out = []
    for t in texts:
        v = [0.0] * DIM
        for w in t.lower().split():
            h = int(hashlib.sha1(w.encode()).hexdigest()[:8], 16)
            v[h % DIM] += 1.0
        n = math.sqrt(sum(x*x for x in v)) or 1.0
        out.append([x/n for x in v])
    return out

def cos(a, b): return sum(x*y for x, y in zip(a, b))

def pct(v, p):
    v = sorted(v); k = max(0, min(len(v)-1, int(round((p/100)*(len(v)-1)))))
    return round(v[k], 2)

def corpus(n_topics=20, n_sections=5):
    docs, chunks, truth_chunk = [], [], []
    for t in range(n_topics):
        secs = [f"topic {t} section {s} keyword K{t}_{s} details about domain {t}" for s in range(n_sections)]
        docs.append(" ".join(secs)); chunks.append(secs)
        for s in range(n_sections):
            truth_chunk.append((t, s))
    return docs, chunks, truth_chunk

def score_docs(qv, dvs, k):
    return sorted(range(len(dvs)), key=lambda i: -cos(qv, dvs[i]))[:k]

def score_chunks_max(qv, cvs, k):
    # cvs: list[list[vec]] per doc -> max cosine across its chunks
    return sorted(range(len(cvs)), key=lambda i: -max(cos(qv, v) for v in cvs[i]))[:k]

def lexical_rerank(q, cand, chunks, k):
    qt = set(q.lower().split())
    def ov(i):
        best = 0
        for c in chunks[i]:
            best = max(best, len(qt & set(c.lower().split())))
        return best
    return sorted(cand, key=lambda i: (-ov(i), cand.index(i)))[:k]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--embed-url", default=os.environ.get("EMBED_URL"))
    ap.add_argument("--embed-model", default=os.environ.get("EMBED_MODEL", "bge-m3"))
    ap.add_argument("--topics", type=int, default=20)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--json-out")
    a = ap.parse_args()
    docs, chunks, truth = corpus(a.topics)
    rnd = random.Random(42)
    qs = [f"find keyword K{t}_{s}" for t, s in rnd.sample(truth, min(len(truth), 40))]
    gt = []
    for q in qs:
        key = q.split("K")[1]
        t, s = key.split("_"); gt.append((int(t), int(s)))
    emb = (lambda x: toy_embed(x)) if not a.embed_url else (lambda x: http_embed(x, a.embed_url, a.embed_model))
    t0 = time.perf_counter(); dv = emb(docs); doc_s = time.perf_counter()-t0
    t0 = time.perf_counter(); cv = [emb(c) for c in chunks]; chunk_s = time.perf_counter()-t0
    qv = emb(qs)
    res = {"docs": len(docs), "chunks": sum(len(c) for c in chunks), "queries": len(qs),
           "dim": len(dv[0]), "doc_embed_ms": round(doc_s*1000, 1), "chunk_embed_ms": round(chunk_s*1000, 1)}
    def acc(ranks, mode):
        r1 = sum(1 for r, (t, s) in zip(ranks, gt) if r and r[0] == t)
        r5 = sum(1 for r, (t, s) in zip(ranks, gt) if t in r)
        return {"recall_at_1": round(r1/len(gt), 3), "recall_at_5": round(r5/len(gt), 3)}
    lat = []
    for name, fn in (("doc", lambda q, i: score_docs(qv[i], dv, a.k)),
                     ("chunk_max", lambda q, i: score_chunks_max(qv[i], cv, a.k))):
        t0 = time.perf_counter(); ranks = [fn(q, i) for i, q in enumerate(qs)]; lat.append((time.perf_counter()-t0)*1000)
        res[name] = acc(ranks, name)
    t0 = time.perf_counter()
    ranks = [lexical_rerank(qs[i], score_chunks_max(qv[i], cv, 10), chunks, a.k) for i in range(len(qs))]
    lat.append((time.perf_counter()-t0)*1000)
    res["chunk_rerank"] = acc(ranks, "chunk_rerank")
    res["latency_ms"] = {"doc": round(lat[0], 1), "chunk_max": round(lat[1], 1), "chunk_rerank": round(lat[2], 1)}
    ok = (res["doc"]["recall_at_5"] >= 0.9 and res["chunk_max"]["recall_at_5"] >= 0.9)
    if a.selftest:
        print("SELFTEST", "PASS" if ok else "FAIL", json.dumps(res, ensure_ascii=False))
        raise SystemExit(0 if ok else 1)
    s = json.dumps(res, ensure_ascii=False, indent=2); print(s)
    if a.json_out: open(a.json_out, "w", encoding="utf-8").write(s+"\n")

if __name__ == "__main__": main()
