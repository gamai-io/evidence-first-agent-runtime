#!/usr/bin/env bash
# One command, no network, no keys. Runs every test and both demos.
set -euo pipefail
cd "$(dirname "$0")"
echo "== proofgate =="
python3 proofgate/tests/run_tests.py | tail -2
python3 proofgate/proofgate.py demo > /tmp/proofgate_demo.json
python3 - <<'PY'
import json
d = json.load(open('/tmp/proofgate_demo.json'))
print("demo:", d['status'], d['counts'], "hash", d['evidence_sha256'][:16])
assert d['counts'] == {'confirmed': 10, 'refuted': 2, 'unverified': 0}
PY

echo "== agent-immunity =="
python3 agent-immunity/tests/run_tests.py | tail -2
python3 agent-immunity/eval.py | tail -12

echo "== crossnode-bench =="
python3 crossnode-bench/tests/run_tests.py | tail -2
python3 crossnode-bench/crossnode.py --demo --runs 1

echo "OK — all components reproduced locally."
