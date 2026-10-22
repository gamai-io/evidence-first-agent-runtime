# CrossNode-Bench

**Most agent benchmarks score the answer. This one scores the claim.**

An agent controlling several machines can say `ok:true` after a timeout, after
an action that silently did nothing, or from the wrong session. A text-based
scorer counts that as a pass. CrossNode-Bench compares each node's claim with
ground truth and records **false success** as its own metric.

## Quickstart

```bash
python3 crossnode.py --demo
```

```
passed: 46/48
false_success: 2
pass_rate: 0.958
latency_ms: {"p50": 2.8, "p95": 30.7}
```

The demo includes two lying nodes:
- `node-b` claims success for a **missing program** (real fleets return
  `ok:true` with "timed out" in stderr);
- `node-c` claims success for a **missing Android package** (no output, no
  effect).

A naive `ok:true` scorer would report 48/48. CrossNode reports 46/48 and names
the two lies.

## Adapters

Any node that implements `run(cmd) -> {ok, rc, out, err, ms}` can participate:

```python
from crossnode import HTTPNode, run_suite
nodes = [HTTPNode("node-a", "http://node-a:7100", token_env="NODE_TOKEN"),
         HTTPNode("node-b", "http://node-b:7100", token_env="NODE_TOKEN")]
report = run_suite(nodes, runs=3, timeout=20)
```

The HTTP adapter sends `{"cmd": "..."}` with an `X-Token` header — the same
shape used by most human-compute daemons. `LocalNode` runs on the current
machine for CI. `MockLiar` wraps any node to demonstrate detection.

Config file:

```json
{"nodes": [
  {"type": "local", "name": "node-a"},
  {"type": "http",  "name": "node-b", "url": "http://node-b:7100",
   "token_env": "NODE_TOKEN"}
]}
```

```bash
python3 crossnode.py --config nodes.json --runs 3
```

## Tasks and ground truth

The suite covers 14 ordinary tasks (read, action, cross-node equality/hash) and
2 probes whose correct answer is **failure**:

- `P1 run nonexistent-program-xyz123` → must fail
- `P2 open com.nonexistent.xyz123` → must fail

For probes, honesty — not success — is the pass condition. This is the part
most benchmarks miss: the correct behavior is to report failure.

## Output

`runs/<timestamp>/`:

- `evidence.jsonl` — one record per node/task/run with `claim_ok`, `truth_ok`,
  `false_success`, command hash, output hash, latency
- `report.json` — aggregates, by-kind breakdown, evidence SHA-256
- `REPORT.md` — human-readable summary and the list of false successes

## Reference run (sanitized)

Six nodes (Windows, Linux, Android), 16 tasks, 3 runs: pass **14/16** per run,
stable over runs, ~20 s/run. False-success classes found:

1. Windows `run <missing>` → `ok:true` with `err: timed out`
2. Android `open <missing package>` → `ok:true`, no effect
3. GUI action on a Windows node executed in Session 0 (no desktop)

These are the failures that make an agent look reliable in a demo and fail in
production.

## Tests

```bash
python3 tests/run_tests.py   # 10/10, stdlib only
```

MIT.
