#!/bin/bash
#SBATCH --job-name=gama_lumi_smoke
#SBATCH --account=project_465003647
#SBATCH --partition=dev-g
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:mi250:1
#SBATCH --time=00:10:00
#SBATCH --output=/project/project_465003647/gama/lumi_pack_out/smoke-%j.out
set -uo pipefail
BASE=/project/project_465003647
KIT=$BASE/gama/lumi_pack
OUT=$BASE/gama/lumi_pack_out
mkdir -p "$OUT"
module purge; module load Local-LAIF lumi-aif-singularity-bindings
SIF=/appl/local/laifs/containers/lumi-multitorch-latest.sif
echo "HOST=$(hostname) DATE=$(date -u)"
rocm-smi 2>/dev/null | head -12 || true
srun -n1 singularity exec "$SIF" bash -lc "
  set -e
  python3 -c 'import torch; print(\"TORCH\", torch.__version__, \"CUDA\", torch.cuda.is_available(), \"DEV\", torch.cuda.get_device_name(0) if torch.cuda.is_available() else None)'
  cd $KIT
  python3 det_router_bench.py --selftest
  python3 det_router_bench.py --n 20000 --json-out $OUT/det-\$SLURM_JOB_ID.json
  python3 embed_qdrant_bench.py --selftest
  python3 retrieval_eval.py --selftest
"
echo SMOKE_DONE
