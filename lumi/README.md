# LUMI — deterministic + retrieval + embedding experiments

Portable, evidence-first benchmarks. No private data, no credentials, no network
required except the optional HTTP embedding endpoint you point it at.

| file | what it measures | deps |
|---|---|---|
| `det_router_bench.py` | risk gate T1/T2 (incl. `obrisi /var/log sve` adjacency), Decimal money math, tool-call JSON recovery | stdlib |
| `embed_qdrant_bench.py` | embed throughput, Qdrant build/search latency, recall@1/@5 | stdlib (HTTP embed + Qdrant REST) |
| `retrieval_eval.py` | BM25 vs dense vs RRF fusion, recall@1/@5, nDCG@5 | stdlib (dense optional) |
| `bench_v2/` | vLLM/harness load gen with TTFT + honest false-success (LUMI job template) | aiohttp |

All scripts support `--selftest` (offline, deterministic).

## Local run (today, measured)
```bash
python3 det_router_bench.py --n 20000
# {"risk_us_per_call":2.885,"math_us_per_call":1.506,"json_recover_us_per_call":3.111,"money_example":"246.50"}

python3 embed_qdrant_bench.py --docs 200 --queries 40
# bge-m3 dim=1024, 5.0 docs/s (CPU), search p50 2.98 ms, recall@5 1.0

EMBED_URL=http://127.0.0.1:8064/v1/embeddings python3 retrieval_eval.py --docs 200 --queries 40
# BM25 1.0 / dense 1.0@5 / RRF 1.0; RRF fixes dense recall@1 0.8 -> 1.0
```

## LUMI
```bash
# 1) copy kit (from Oracle, cert valid)
scp -i ~/.ssh/id_EFP -o IdentitiesOnly=yes \
  -o CertificateFile=~/.ssh/id_efp.lumi.csc.fi-cert.pub -r lumi/ \
  ${LUMI_USER:-your-user}@efp.lumi.csc.fi:/project/project_465003647/gama/lumi_pack/

# 2) GPU smoke (1 GCD) or full bench (4 GCD)
ssh ... ${LUMI_USER:-your-user}@efp.lumi.csc.fi 'cd /project/project_465003647/gama/lumi_pack && sbatch run_lumi_smoke.sbatch'
ssh ... ${LUMI_USER:-your-user}@efp.lumi.csc.fi 'cd /project/project_465003647/gama/lumi_pack/bench_v2 && sbatch serve_and_bench.sbatch'
```
Environment: `module load Local-LAIF lumi-aif-singularity-bindings`,
`SIF=/appl/local/laifs/containers/lumi-multitorch-latest.sif`.

## Deterministic guard (optional, `--guard`)
`run_bench.py --guard` runs the same pre-LLM rules as GAMA FastPath (T1/T2 risk,
injection/env, PDV, X% od Y with Decimal half-up) and only sends the rest to the
model. It is honest: guarded rows are marked `guard: true`, `ms=0`.

Measured (1k, same model/seed, CONC=128):
| run | false_success |
|---|---:|
| raw model (23426096) | 197 (19.7%) |
| guard v1 (23443568) | 7 (0.7%) |
| guard v2 (23443668) | 1 (0.1%) |
| guard v3 (+ mass-mail) (23443907) | **0 (0.0%) — PASS** |

## Rules
- Deterministic seeds, `temperature=0`, fixed prompt set (hash in meta).
- A model claim only counts with proof; refusal/honest-unknown is a pass.
- Do not publish internal endpoints, hosts, customer data, or keys.

**Zenodo v1.2.2:** DOI `10.5281/zenodo.23933835` (concept `10.5281/zenodo.23920505`)
