#!/usr/bin/env bash
# Offline after dependencies are installed: runs every test, MCP selftest,
# held-out smoke and both demos.
set -euo pipefail
cd "$(dirname "$0")"
python3 - <<'PY'
import importlib.util, sys
missing = [m for m in ("proofgate_runtime", "gamai_trust", "gamai_guard",
                     "crossnode", "effect_lease")
           if importlib.util.find_spec(m) is None]
if missing:
    sys.exit("missing canonical packages: %s\nrun: python3 -m pip install -r "
             "requirements-vendored.txt" % ", ".join(missing))
PY

echo "== proofgate =="
python3 tests/suites/proofgate_core.py | tail -2
python3 tests/suites/proofgate_adversarial.py | tail -5
python3 -c "import json; from proofgate_runtime import demo; json.dump(demo(), open('/tmp/proofgate_demo.json','w'))"
python3 - <<'PY'
import json
d = json.load(open('/tmp/proofgate_demo.json'))
print("demo:", d['status'], d['counts'], "hash", d['evidence_sha256'][:16])
assert d['counts'] == {'confirmed': 10, 'refuted': 2, 'unverified': 0}
PY

echo "== agent-immunity =="
python3 agent-immunity/tests/run_tests.py | tail -2
python3 agent-immunity/eval.py | tail -12

echo "== T1 det-seq =="
python3 labs/det_seq.py | tail -10

echo "== T2 ecc/hash =="
python3 labs/ecc_hash.py | tail -12

echo "== T3 chladni =="
python3 labs/chladni.py | tail -8

echo "== gamai-guard =="
python3 -m gamai_guard.tests.run_tests | tail -2

echo "== I Ching/codon negative control =="
python3 labs/iching_codons.py | tail -5

echo "== polymorph E1 (installed package) =="
python3 -m run_e1 | tail -12
python3 -m run_e2 | tail -6
python3 bench/polymorph_e3.py | tail -8

echo "== provenance =="
python3 tests/suites/proofgate_provenance.py | tail -2

echo "== mcp =="
python3 -m gamai_trust.mcp_server --selftest

echo "== held-out (20) =="
python3 bench/run_heldout.py --limit 20 --out /tmp/heldout_smoke.json | tail -8

echo "== edge corpus =="
python3 bench/run_edge.py | tail -6

echo "== crossnode-bench (installed package) =="
python3 -m crossnode --demo --runs 1 --outdir /tmp/crossnode_demo > /tmp/crossnode_demo.json
python3 - <<'PY'
import json
d = json.load(open('/tmp/crossnode_demo.json'))
assert d['records'] == 48 and d['passed'] == 46 and d['false_success'] == 2, d
print("demo: %d/%d passed, %d false successes" % (d['passed'], d['records'], d['false_success']))
PY
python3 -m crossnode --verify-report /tmp/crossnode_demo/report.json > /tmp/crossnode_verify.json
python3 - <<'PY'
import json
v = json.load(open('/tmp/crossnode_verify.json'))
assert v['ok'] and v['counts']['records'] == 48, v
print("report verified:", v['counts'])
PY

echo "OK — all components reproduced locally."
