#!/usr/bin/env python3
"""Embedding + Qdrant bench (portable; works on LUMI CPU/GPU or any HTTP embedder).

Measures: embed throughput, build time, p50 search latency, recall@1/@5.
Backends: OpenAI-compatible /v1/embeddings (EMBED_URL) + Qdrant REST (QDRANT_URL).
Offline selftest needs no network and no third-party packages.

  python3 embed_qdrant_bench.py --selftest
  EMBED_URL=http://127.0.0.1:8064/v1/embeddings QDRANT_URL=http://127.0.0.1:6333 \
    python3 embed_qdrant_bench.py --docs 200 --queries 40
  python3 embed_qdrant_bench.py --selftest --json-out out.json
"""
import argparse, hashlib, json, math, os, random, statistics, time, urllib.request

DIM_HTTP_DEFAULT = 1024

def post_json(url, obj, timeout=300, method="POST"):
    data = json.dumps(obj).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())

class HTTPEmbedder:
    def __init__(self, url, model):
        self.url, self.model = url, model
    def embed(self, texts):
        out = []
        for i in range(0, len(texts), 16):
            batch = texts[i:i+16]
            r = post_json(self.url, {"model": self.model, "input": batch})
            out.extend([x["embedding"] for x in r["data"]])
        return out

class ToyEmbedder:
    """Deterministic topic-aware vectors for offline selftest (dim=32)."""
    def __init__(self, topics): self.topics, self.dim = topics, 32
    def embed(self, texts):
        out = []
        for t in texts:
            v = [0.0] * self.dim
            for w in t.lower().split():
                if w.isdigit():
                    v[int(w) % self.dim] += 1.0
            n = math.sqrt(sum(x*x for x in v)) or 1.0
            out.append([x/n for x in v])
        return out

def cos(a, b): return sum(x*y for x, y in zip(a, b))

class Qdrant:
    def __init__(self, base, name):
        self.base, self.name = base.rstrip("/"), name
    def create(self, dim):
        post_json(f"{self.base}/collections/{self.name}", {"vectors": {"size": dim, "distance": "Cosine"}}, method="PUT")
    def upsert(self, points):
        post_json(f"{self.base}/collections/{self.name}/points?wait=true", {"points": points}, method="PUT")
    def search(self, vec, k=5):
        r = post_json(f"{self.base}/collections/{self.name}/points/search", {"vector": vec, "limit": k, "with_payload": True})
        return r["result"]
    def drop(self):
        try: post_json(f"{self.base}/collections/{self.name}", None, method="DELETE")
        except Exception: pass

class MemStore:
    def __init__(self): self.pts = []
    def create(self, dim): pass
    def upsert(self, points): self.pts.extend(points)
    def search(self, v, k=5): return sorted(({"id": p["id"], "score": cos(v, p["vector"]), "payload": p["payload"]} for p in self.pts), key=lambda x: -x["score"])[:k]
    def drop(self): pass

def corpus(n_docs, n_queries):
    docs = [f"document {i} about topic {i % 20} with deterministic filler text" for i in range(n_docs)]
    queries = [f"what is topic {i % 20}" for i in range(n_queries)]
    truth = [i % 20 for i in range(n_queries)]
    return docs, queries, truth

def pct(v, p):
    if not v: return None
    v = sorted(v); k = max(0, min(len(v)-1, int(round((p/100)*(len(v)-1)))))
    return round(v[k], 2)

def evaluate(embedder, store, docs, queries, truth, k=5):
    t0 = time.perf_counter(); dv = embedder.embed(docs); build_embed = time.perf_counter()-t0
    dim = len(dv[0]); store.create(dim)
    t0 = time.perf_counter()
    store.upsert([{"id": i, "vector": dv[i], "payload": {"doc": i, "topic": i % 20}} for i in range(len(docs))])
    build_store = time.perf_counter()-t0
    t0 = time.perf_counter(); qv = embedder.embed(queries); q_embed = time.perf_counter()-t0
    lat, r1, r5 = [], 0, 0
    for q, vec, topic in zip(queries, qv, truth):
        t0 = time.perf_counter(); hits = store.search(vec, k); lat.append((time.perf_counter()-t0)*1000)
        topics = [h["payload"].get("topic") for h in hits]
        r1 += 1 if topics and topics[0] == topic else 0
        r5 += 1 if topic in topics else 0
    nq = len(queries)
    return {"docs": len(docs), "dim": dim, "embed_docs_s": round(build_embed, 3),
            "doc_embed_per_s": round(len(docs)/build_embed, 1) if build_embed else None,
            "build_store_s": round(build_store, 3), "query_embed_s": round(q_embed, 3),
            "search_ms_p50": pct(lat, 50), "search_ms_p95": pct(lat, 95),
            "recall_at_1": round(r1/nq, 3), "recall_at_5": round(r5/nq, 3), "n_queries": nq}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--docs", type=int, default=200)
    ap.add_argument("--queries", type=int, default=40)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--embed-url", default=os.environ.get("EMBED_URL", "http://127.0.0.1:8064/v1/embeddings"))
    ap.add_argument("--embed-model", default=os.environ.get("EMBED_MODEL", "bge-m3"))
    ap.add_argument("--qdrant-url", default=os.environ.get("QDRANT_URL", "http://127.0.0.1:6333"))
    ap.add_argument("--collection", default="lumi_bench_tmp")
    ap.add_argument("--json-out")
    a = ap.parse_args()
    docs, queries, truth = corpus(a.docs, a.queries)
    if a.selftest:
        res = evaluate(ToyEmbedder(range(20)), MemStore(), docs, queries, truth, a.k)
        ok = res["recall_at_5"] >= 0.9 and res["recall_at_1"] >= 0.9
        print("SELFTEST", "PASS" if ok else "FAIL", json.dumps(res, ensure_ascii=False))
        raise SystemExit(0 if ok else 1)
    st = Qdrant(a.qdrant_url, a.collection)
    try:
        res = evaluate(HTTPEmbedder(a.embed_url, a.embed_model), st, docs, queries, truth, a.k)
        res["backend"] = "http+qdrant"; res["embed_model"] = a.embed_model
    finally:
        st.drop()
    out = json.dumps(res, ensure_ascii=False, indent=2)
    print(out)
    if a.json_out: open(a.json_out, "w", encoding="utf-8").write(out+"\n")

if __name__ == "__main__": main()
