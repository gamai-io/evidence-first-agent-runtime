# Evidence-first agent runtime

Three small, dependency-free components for agents that must be **provable**,
**hard to hijack**, and **honest about failure**:

| Component | What it answers | Measured result |
|---|---|---|
| **[proofgate](proofgate/)** | "Did it actually happen?" | 10 confirmed + 2 refuted + 0 unverified on the built-in suite; tamper-evident SHA-256 |
| **[agent-immunity](agent-immunity/)** | "Has this attack been seen before?" | injection success 100% → **0%** by round 3, utility 100%, false denial 0%, ~1.3 ms/check |
| **[crossnode-bench](crossnode-bench/)** | "Does the agent lie about other machines?" | demo detects **2 false successes** that a naive `ok:true` scorer would count as passes |

The thesis is simple: **capability is no longer the bottleneck — trust is.**
A runtime that can prove an action, remember a refusal, and measure its own
false-success rate is more useful than one that is merely fast.

## Quickstart

```bash
git clone <this repo> && cd evidence-first-agent-runtime
./repro.sh
```

`repro.sh` runs every test suite and both demos. No network, no database, no
API keys. Python 3.10+ standard library only.

```bash
# 1. prove/disprove claims
python3 proofgate/proofgate.py demo

# 2. learn antibodies from injections
python3 agent-immunity/immunity.py selftest < /dev/null
python3 agent-immunity/eval.py

# 3. detect lying nodes
python3 crossnode-bench/crossnode.py --demo
```

## Evidence (all measured, all reproducible)

- **proofgate**: 16/16 tests; demo returns `confirmed=10, refuted=2,
  unverified=0`; changing any claim after emission makes `verify` report
  `tampered=true`; missing/malformed evidence is `unverified`, never
  `confirmed`.
- **agent-immunity**: 28/28 tests. On a 10-payload × 3-channel × 3-round
  synthetic corpus: baseline ASR **100%**, filter-only **0% / 10% / 0%**
  (a reworded payload escapes), antibody memory **0% / 0% / 0%**, utility
  **100%**, false denial **0%**, guard **~1.3 ms**. A reference run with a
  harder corpus measured 3.3% → 0% → 0% and 1.55 ms.
- **crossnode-bench**: 10/10 tests; demo **46/48 pass, 2 false successes**
  across three nodes. A reference run on a real heterogeneous fleet
  (Windows/Linux/Android, six nodes, 16 tasks × 3 runs) reproduced three
  classes of false success: a missing program reported `ok:true`, a missing
  Android package reported `ok:true`, and a GUI action executed in the wrong
  session.
- **Runtime context** (the harness these components came from): 202 native
  tools, 18/18 MCP servers alive, 8 plugins, per-request budget cap, no
  degraded subsystems. Code bench 6/6 at ~2.0 s/task on our tasks; pass@1 and
  pass@3 = 1.0 on 20 tasks (n=3), **$0.00172 per solved task**. Small N, our
  tasks — treat as directional, not universal.

## Why this is different

Most agent stacks optimize *what the model can do*. These components optimize
*what you can trust*:

1. **Refusal is a first-class output.** `refuted` and `unverified` are not
   errors; they are the correct answer when evidence is absent.
2. **A block becomes an antibody.** The defense improves with every attack
   instead of waiting for a new model release.
3. **Honesty is benchmarked.** False success is a metric, not an anecdote.
4. **Isolation is priced.** The same task can run under bubblewrap, runc,
   seccomp, or gVisor, and the latency/cost of each level is recorded (see the
   companion design note in `launch/`).

## Limitations (read this before quoting numbers)

- The injection corpus is synthetic. An adaptive attacker who knows the
  patterns is not covered; near-miss matching can false-positive on long
  shared phrasing. Measure on your traffic before relying on it.
- `proofgate` checks predicates over evidence supplied by the caller. It does
  not turn a vague claim into a formal one for you; decompose the claim first.
- `crossnode-bench`'s demo uses a local shell plus mocked lying nodes. The
  reference fleet run is real, but node names and addresses are removed.
- Harness benchmarks are small-N and single-model. They show direction, not a
  leaderboard position.

## License

MIT. See [LICENSE](LICENSE).
