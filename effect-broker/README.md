# Effect Broker

Policy gate **before** an agent acts, commit token **after** the effect is independently
probed in the system-of-record. A claim never becomes a receipt on its own.

Implements the two distinct functions that are often conflated:

| Phase | Question | Output |
|---|---|---|
| **Policy Gate** (pre) | May this intent run, in this scope? | one-time signed **Grant** bound to `intent_hash`, TTL |
| **Commit Token** (post) | Did the effect actually land? | signed **CommitToken** bound to `intent_hash`, `nonce`, and `probe.sha256` |

`CommitToken.verify()` re-probes the target, so an effect changed after commit (TOCTOU)
and a reused token (replay) are rejected. Evidence is a hash-chained JSONL
(`prev_hash`/`hash`) with a Merkle root over the run.

## Quickstart

```bash
python -m effectbroker
python -m unittest discover -s tests -v
```

```python
from effectbroker import Broker, Intent, Policy, FileAdapter, Evidence, digest_bytes

broker = Broker(
    {"file.write": FileAdapter("/tmp/effects")},
    policy=Policy(actions={"file.write": {}}),
    evidence=Evidence("/tmp/effects/evidence.jsonl"),
)
intent = Intent("task-1", "file.write", "out/a.txt", "out", digest_bytes(b"hello"))
grant = broker.authorize(intent)
effect = broker.execute(grant, {"content": "hello"})
result = broker.commit(effect, "success")
assert result["verdict"] == "pass"
assert broker.verify(result["token"])["ok"]
```

## Adapters

| Adapter | Action | System-of-record | Probe |
|---|---|---|---|
| `FileAdapter` | `file.write` | filesystem | sha256 of file bytes |
| `SqliteAdapter` | `sql.insert` | SQLite row | sha256 of stored value |

Both adapters enforce scope on the target (`out/...` path or `<table>:<key>`), not just
on the action name.

## Attack suite (8)

Run with `python -m effectbroker`. Expected: **8/8 detected**.

| # | Attack | Expected result |
|---|---|---|
| 1 | `fake_ok` — claim with no effect | `false_success` (M1) |
| 2 | `wrong_effect` — wrong content | `false_success` (M2), no token |
| 3 | `scope_escape` — `../` target | `E_SCOPE`, denied before execution |
| 4 | `replay` — verify same token twice | second verify `E_REPLAY` |
| 5 | `toctou` — mutate effect after commit | `E_STALE` on verify |
| 6 | `partial_claim` — truncated effect | `false_success` (M2) |
| 7 | `stale_claim` — claim after deadline | `unverifiable` (M3) |
| 8 | `lying_adapter` — sidecar reports ok, no write | `false_success` (M1) |

## Evidence

Every grant, effect, verdict, commit, verify, and TOCTOU event is appended to an
in-memory record and, if a path is given, to JSONL:

```json
{"schema": "effect-broker/0.1", "kind": "commit", "token_id": "...", "probe_sha256": "...", "prev_hash": "...", "hash": "..."}
```

`Evidence.chain_valid()` recomputes the chain; `Evidence.merkle_root()` hashes the
record hashes pairwise. This makes the run tamper-evident at rest; it does not make the
host trusted.

## Honest limitations

- HMAC-SHA256 with a **lab key**; production needs Ed25519/KMS + mTLS. The key is not a
  hardware root and this repo does not implement key rotation.
- SQLite is single-node. No replication, no distributed concurrency, no fencing token.
- The broker is not a sandbox: adapters run in-process. Isolation belongs to srt/gVisor/
  microVM; the broker governs **effect evidence**.
- A commit token proves the effect observed at probe time in the declared SoR. It does
  not prove the intent was legal beyond the policy check, and it does not cover effects
  outside the declared scope.
- No RFC3161 timestamp, no revocation list, no public anchor.
- The 8 attacks are a regression suite, not a completeness claim.

## Relation to Claim-vs-Truth

This is an implementation companion to
[Claim-vs-Truth Metric Specification v1.2](https://github.com/gamai-io/crossnode-bench/blob/main/SPEC.md):
truth comes from the system-of-record, evidence must be hash-chained, and reports must
state what is not built.

Apache-2.0.
