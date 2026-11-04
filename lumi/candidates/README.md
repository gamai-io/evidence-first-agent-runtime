# Candidates — portable benches (synthetic, no private data)

| file | measures | deps |
|---|---|---|
| `rerank_chunk_bench.py` | doc vs chunk-max vs chunk+lexical rerank: recall@1/@5, embed/latency | stdlib + optional HTTP embed |
| `cbr_skill_bench.py` | skill matcher (500 skills) + CBR store (1000 cases): acc@1, hit@3, ms | stdlib |

Both run fully offline with `--selftest` (deterministic toy data) and with a real
embedder via `EMBED_URL` (`/v1/embeddings`).

## Measured (Contabo, 2026-11-04)

Real bge-m3 (HTTP, CPU, 1024d): doc recall@1 **0.875** / @5 1.0; chunk-max **1.0/1.0**;
chunk+rerank **1.0/1.0**; embed 20 docs 8.1 s, 100 chunks 14.3 s; search 27.7 / 144.8 / 150.9 ms.
Skill matcher **1.0 acc@1**, 0.769 ms/q; CBR **1.0 hit@3**, 3.079 ms/q.
- rerank toy: doc recall@1 0.175 / @5 0.90; chunk-max 0.325/0.925; **chunk+rerank 0.975/0.975**.
- skill matcher: **acc@1 1.0**, 0.906 ms/query (500 skills).
- CBR: **hit@3 1.0**, 3.323 ms/query (1000 cases, in-memory SQLite).
