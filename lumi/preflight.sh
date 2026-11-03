#!/bin/sh
# Read-only preflight: local scripts, LUMI cert, project path.
set -u
echo "== selftests =="
python3 det_router_bench.py --selftest || exit 1
python3 embed_qdrant_bench.py --selftest || exit 1
python3 retrieval_eval.py --selftest || exit 1
echo "== LUMI cert =="
CERT="$HOME/.ssh/id_efp.lumi.csc.fi-cert.pub"
[ -f "$CERT" ] && ssh-keygen -L -f "$CERT" | head -8 || echo "NO CERT"
echo "== remote =="
ssh -i "$HOME/.ssh/id_EFP" -o IdentitiesOnly=yes -o CertificateFile="$CERT" \
  -o StrictHostKeyChecking=no ${LUMI_USER:-your-user}@efp.lumi.csc.fi \
  'hostname; ls -d /project/project_465003647/gama 2>/dev/null; which sbatch' || exit 1
