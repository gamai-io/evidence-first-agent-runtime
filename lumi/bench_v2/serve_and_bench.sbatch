#!/bin/bash
#SBATCH --job-name=gama_bench_v2
#SBATCH --account=project_465003647
#SBATCH --partition=dev-g
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=56
#SBATCH --gres=gpu:mi250:4
#SBATCH --time=01:30:00
#SBATCH --output=/project/project_465003647/gama/out/bench_v2-%j.out
#SBATCH --signal=B:TERM@300

set -uo pipefail
BASE=/project/project_465003647
KIT=$BASE/gama/bench_v2
OUT=$BASE/gama/out
MODEL=${MODEL:-/scratch/project_465003647/models/qwen25-7b}
PORT=${PORT:-8000}
N=${N:-1000}
CONC=${CONC:-128}
mkdir -p "$OUT"
trap 'sync; echo TERM > "$OUT/term_$SLURM_JOB_ID"; pkill -f "vllm.entrypoints" 2>/dev/null; true' TERM

module purge
module load Local-LAIF lumi-aif-singularity-bindings
SIF=/appl/local/laifs/containers/lumi-multitorch-latest.sif

echo "HOST=$(hostname) DATE=$(date -u) MODEL=$MODEL N=$N CONC=$CONC"
rocm-smi 2>/dev/null | head -20 || true

# 1) vLLM server (4 GCD, TP4). Ako padne, job pada — fallback je TP2.
srun -n1 --gres=gpu:mi250:4 --cpus-per-task=32 singularity exec -B /scratch:/scratch "$SIF" \
  python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL" --host 127.0.0.1 --port "$PORT" \
    --tensor-parallel-size 4 --max-model-len 32768 \
    --max-num-seqs 256 --enable-prefix-caching \
    > "$OUT/vllm_$SLURM_JOB_ID.log" 2>&1 &
VLLM_PID=$!

for i in $(seq 1 150); do
  curl -sf "http://127.0.0.1:$PORT/v1/models" >/dev/null && break
  sleep 2
done
if ! curl -sf "http://127.0.0.1:$PORT/v1/models" >/dev/null; then
  echo "VLLM_FAIL"; tail -80 "$OUT/vllm_$SLURM_JOB_ID.log"; exit 2
fi
echo "VLLM_READY"

# 2) model-plane bench (generator u istom allotmentu, drugi step)
srun --overlap --jobid="$SLURM_JOB_ID" -n1 --cpus-per-task=8 singularity exec -B /scratch:/scratch "$SIF" \
  python3 "$KIT/run_bench.py" --mode model --url "http://127.0.0.1:$PORT" \
    --set model_plane --n "$N" --conc "$CONC" --warmup 8 --seed 42 \
    --out "$OUT/model_${N}_$SLURM_JOB_ID.jsonl" --summary-out "$OUT/model_${N}_$SLURM_JOB_ID.summary.json"

# 3) provjera
python3 "$KIT/check_results.py" --jsonl "$OUT/model_${N}_$SLURM_JOB_ID.jsonl" \
  --expect-n "$N" --strict --md "$OUT/model_${N}_$SLURM_JOB_ID.md" \
  --json-out "$OUT/model_${N}_$SLURM_JOB_ID.check.json" || echo "CHECK_FAIL"

# 4) GPU-h i čišćenje
sacct -j "$SLURM_JOB_ID" --format=JobID,State,Elapsed,AllocTRES%60
lumi-workspaces 2>/dev/null | tail -8 || true
kill "$VLLM_PID" 2>/dev/null || true
wait 2>/dev/null || true
echo BENCH_DONE
