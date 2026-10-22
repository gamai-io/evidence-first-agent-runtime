# Architecture

The trust layer is three independent components with one shared rule: a claim
is only as good as the evidence attached to it. There is no model in the trust
path.

## Context

```
                 untrusted text / tool output
                              |
                              v
  +-------------------+   +-------------------+   +-------------------+
  |  agent-immunity   |   |     proofgate     |   |  crossnode-bench  |
  |  (before action)  |   |  (after action)   |   |  (across nodes)   |
  +---------+---------+   +---------+---------+   +---------+---------+
            |                       |                       |
            v                       v                       v
      allow / block          confirmed/refuted/       false-success
      + antibody             unverified + hash        metric + evidence
            |                       |                       |
            +-----------+-----------+-----------+-----------+
                        |                       |
                        v                       v
                 CLI / Python API          MCP (stdio)
```

`proofgate` and `agent-immunity` do not call each other. A harness can use
either one alone. `crossnode-bench` consumes any node adapter that returns
`{ok, rc, out, err}`.

## Components

### proofgate

- Input: a list of claims, each with `text`, `predicate`, `observed`,
  `expected`.
- Predicates: `eq_num`, `eq_str`, `hash_eq`, `rc_zero`, `contains`,
  `json_field_eq`.
- Output: per-claim status, aggregate status, counts, timestamp, and
  `evidence_sha256`.
- Aggregation is fail-closed: any `refuted` -> `refuted`; else any
  `unverified` -> `unverified`; only all-confirmed -> `confirmed`.
- `verify(report)` recomputes the hash. A mismatch sets `tampered=true`.
- Optional provenance: HMAC-SHA256 (stdlib) or Ed25519 (optional
  `cryptography`). The signature covers the report including the evidence
  hash; the signature field itself is excluded from the hash.

### agent-immunity

- Two stores in one SQLite file: provenance taint and antibody memory.
- Taint is monotonic: a child inherits the dirtiest parent and cannot be
  cleaner. Tainted memory expires.
- Every blocked injection becomes an antibody signature. Matching is exact
  (canonical SHA-256) plus near-miss (Jaccard/overlap) after NFKC, zero-width
  and bidi stripping, confusable folding, and base64 decoding.
- Antibodies decay; stale signatures become dormant instead of blocking
  forever.
- `shield_check` returns `allow`, `reason`, `attack_class`, `risk`, and a
  normalized hash. Risky tools (`shell`, `fs_write`, `memory_write`, `send`)
  do not get the analytical-context bypass.

### crossnode-bench

- Node adapter contract: `run(cmd) -> {ok, rc, out, err}`.
- A task has a command, a kind (`read`, `action`, `cross`, `probe`), and a
  ground-truth predicate.
- A node claim is scored against ground truth, not against the answer text.
- `claim_ok and not truth_ok` is a **false success**; that is the metric the
  demo is designed to expose.

## Trust boundaries

| Boundary | What crosses it | Assumption |
|---|---|---|
| Model -> harness | text, tool calls | untrusted |
| Tool -> harness | stdout, rc, files | untrusted until checked |
| Caller -> proofgate | `observed` evidence | must come from outside the model |
| Node -> bench | `ok`, `rc`, `out`, `err` | untrusted; ground truth is independent |
| Signer -> verifier | report + signature | key custody is external |
| MCP client -> server | JSON-RPC | local/trusted transport; tool args are untrusted |

## Deployment

- Python 3.10+ standard library for the core. No network, no database, no API
  keys for `./repro.sh`.
- Optional MCP server over stdio (`gamai-trust-mcp`), no listening port.
- Antibody store is a local SQLite file; override with `GAMAI_TRUST_DB`.
- CI runs the full repro on GitHub-hosted runners (Python 3.10/3.11/3.12).

## Non-goals

- Not a model-level safety filter.
- Not a formal verification system.
- Not a substitute for an independent security audit.
- Not a guarantee that `observed` evidence is truthful; it checks the
  predicate over the evidence it is given.
