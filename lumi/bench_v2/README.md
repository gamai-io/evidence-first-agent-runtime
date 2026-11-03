# LUMI bench v2 — kit

Fiksni, ponovljivi benchmark za GAMA harness i vLLM na LUMI-ju. Bez keša, bez lažnog uspjeha, sa TTFT-om i JSONL dokazom.

## Sadržaj
- `prompts_v1.json` — fiksni setovi: `model_plane` (12), `fair10` (10), `human` S1/S2/S3, `p0` (18).
- `run_bench.py` — async loadgen (model ili harness), TTFT, retry odvojen, JSONL, resume, `--selftest`.
- `check_results.py` — schema, reconciliation, p50/p95/p99, false-success, PASS/FAIL.
- `results.schema.json` — schema jednog reda.
- `serve_and_bench.sbatch` — template za jedan LUMI job (vLLM + bench u istom allotmentu).
- `preflight.sh` — 8 checkova prije testa (Oracle/cert/LUMI/harness).

## Brzi start (bez LUMI-ja)
```bash
cd /root/gamaos/lumi_bench
python3 run_bench.py --selftest
# očekivano: SELFTEST PASS: rows=24 ...
python3 check_results.py --jsonl /tmp/lumi_bench_selftest.jsonl --expect-n 24 --strict
```

## Na LUMI-ju (unutar joba)
```bash
# 1) stigati kit na /project (jednom, sa Oracle)
rsync -av -e "ssh -i ~/.ssh/id_EFP -o IdentitiesOnly=yes -o CertificateFile=~/.ssh/id_efp.lumi.csc.fi-cert.pub" \
  /root/gamaos/lumi_bench/ ${LUMI_USER:-your-user}@efp.lumi.csc.fi:/project/project_465003647/gama/bench_v2/

# 2) job (vidi serve_and_bench.sbatch)
sbatch /project/project_465003647/gama/bench_v2/serve_and_bench.sbatch

# 3) provjera
python3 check_results.py --jsonl /project/.../out/run1.jsonl --expect-n 1000 --strict --md /project/.../out/table.md
```

## Pravila mjerenja
- `temperature=0`, `seed=42`, fiksni `prompts_v1.json`; hash seta u meta.
- Unique suffix po zahtjevu (`--unique 1`) da semantički/prefix keš ne iskrivi latenciju.
- Generator **u istom allotmentu**, drugi `srun` step; nikad na login nodu.
- Retry (429/5xx/timeout) se loguje kao isti `i`; ne ulazi u p95 jer se računa samo `ok`.
- `false_success` se računa samo gdje je provjerljivo (exact/number/refuse/honest). Za `task` u model-plane modu je `null` — model nema alate, pa nije fer zvati to lažnim uspjehom.
- `check_results.py --strict` vraća 1 ako: false_success>0, prazan 200, duplikat, schema greška, ili count ≠ expect.

## Skaliranje
```bash
# model-plane: 10k direkt vLLM
python3 run_bench.py --mode model --url http://127.0.0.1:8000 --n 10000 --conc 512 --out out/model10k.jsonl

# harness-plane: 1k kroz 4-8 replika iza nginx (jedna replika = jedan proces)
python3 run_bench.py --mode harness --url http://127.0.0.1:7125 --n 1000 --conc 128 --token "$GAMA_HARNESS_TOKEN" --out out/harness1k.jsonl
```
**Ne tvrdi 10k kroz jedan harness** — to je model-plane test. Harness ima `ThreadingHTTPServer`, 10 GB cap i thread-per-connection.

## Dokaz
Svaki red nosi `prompt_sha`, `status`, `ms`, `ttft_ms`, `false_success`, `text` (500 znakova). `check_results.py` daje `verdict PASS/FAIL`; u izvještaj ide i `sha256sum` JSONL-a.
