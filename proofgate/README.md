# proofgate

**An agent should not be allowed to say "done" without evidence.**

`proofgate` takes claims — `observed` vs `expected` under a predicate — and
returns one of three statuses per claim, plus a SHA-256 that binds the whole
report:

- `confirmed` — evidence is present and the predicate holds
- `refuted` — evidence is present and the predicate does **not** hold
- `unverified` — evidence is missing, malformed, or the predicate is unknown

Aggregation is fail-closed: any `refuted` → `refuted`; else any `unverified`
→ `unverified`; only all-confirmed becomes `confirmed`. No claims → `unverified`.

## Why not just ask the model to check itself?

Self-checking is still a claim. A gate needs (a) an external observation,
(b) a deterministic predicate, and (c) a tamper-evident record. That is what
this 300-line module provides.

## Quickstart

```bash
python3 proofgate.py demo
```

```
status: refuted
counts: {'confirmed': 10, 'refuted': 2, 'unverified': 0}
evidence_sha256: <64 hex>
```

The demo deliberately contains two false claims; a gate that returns
"all good" would be broken.

## API

```python
from proofgate import check, verify, evaluate

report = check([
    {"text": "invoice total", "predicate": "eq_num", "observed": "1170.00", "expected": 1170},
    {"text": "tests passed", "predicate": "rc_zero", "observed": 0},
    {"text": "file digest", "predicate": "hash_eq", "observed": digest, "expected": digest},
])
assert report["status"] in ("confirmed", "refuted", "unverified")
assert verify(report)["ok"]  # recomputes the hash
```

Predicates: `eq_num` (Decimal, 1e-9 tolerance), `eq_str` (whitespace-normalized,
case-folded), `hash_eq` (hex or sha256 of non-hex), `rc_zero`, `contains`,
`json_field_eq` (recursive subset).

CLI:

```bash
python3 proofgate.py check claims.json
python3 proofgate.py verify report.json   # tamper check
```

## Integration patterns

**Before the agent is allowed to answer**, decompose its claim:

```python
observed = run_command("pytest -q")          # rc, stdout
report = check([{"text": "tests pass", "predicate": "rc_zero",
                 "observed": observed.returncode}])
if not report["ok"]:
    reply = "I could not confirm that: %s" % report["status"]
```

**For a fleet**, adapt any node to return `{ok, rc, out, err}` and feed those
fields into `observed`. The gate does not need to know how the observation was
produced; it needs the observation to be external to the model.

**As an MCP tool**, expose `check(claims)` and `verify(report)`. Keep the tool
`side_effect: none`.

## What it does not do

- It does not verify semantic truth. "The customer is happy" is not a
  predicate; decompose it into measurable observations.
- It does not fetch evidence. A caller that passes model output as `observed`
  has defeated the gate.
- It does not protect the evidence source. Pair it with provenance/taint
  tracking (see `agent-immunity`).

## Tests

```bash
python3 tests/run_tests.py   # 16/16, stdlib only
```

MIT.
