# GAMACODE harness receipts — measured 2026-10-29

The harness already signs every tool call (`GTL_RECEIPT_V1`), so the first
layer of the trust story is live, not aspirational.

## Measurements

```text
GET /gtl/stats
{"receipts": 801, "seq": 799, "chained": true, "signed": true,
 "key_id": "b04f903a64d346df", "keys": ["b04f903a64d346df","f682e767921975dc"],
 "require_signature": true}
```

Latest record (`make_report`, seq 799):

```text
id      b7780976e981a313
hash    b7780976e981a313ac11f2dc010274fd1be87ae5e50601fdc248027da39d19bb
chain   239bc1ad1b036f2ad85629e2fcf6285a5063ac0a2c5963a3255c3a8bef64230d
sig     ed25519 / b04f903a64d346df
```

## Verify and tamper test

`POST /gtl/verify` with `X-Token`:

- original receipt -> `ok:true`, `hash_ok:true`, `signature_ok:true`
- one changed payload field -> `ok:false`, `hash_ok:false`, `signature_ok:false`

This is an independent check over the receipt body; it does not trust the
agent's narration.

## What is still missing

GTL receipts prove **what the harness recorded**. They do not yet provide:

- a scoped capability grant before execution,
- a fencing lease for concurrent writers,
- an external anchor/inclusion proof,
- a fail-closed approval flow for irreversible actions.

That is exactly the gap SIGIL should close. The integration target is:
`GTL receipt -> SIGIL grant/lease -> external anchor`, without changing the
existing receipt format or breaking tool calls.

## Reproduce

```bash
TOKEN=$(grep '^GAMA_HARNESS_TOKEN=' /etc/gama-harness.env | cut -d= -f2-)
curl -s -H "X-Token: $TOKEN" http://127.0.0.1:7125/gtl/stats
curl -s -H "X-Token: $TOKEN" http://127.0.0.1:7125/gtl/pubkey
```

## SIGIL grant before the effect (live, 2026-10-29)

`gama_sigil_guard.py` is now enabled for `shell` and `run` through a systemd
drop-in (`/etc/systemd/system/gama-harness.service.d/zz-sigil-guard.conf`).
For those tools the order is:

```
grant -> authorize -> execute -> record -> verify
```

The guard is fail-closed when `SIGIL_GUARD_ENFORCE=1`. The SIGIL receipt is
attached to the tool result as `_sigil`.

Live proof through the harness itself:

```bash
TOKEN=$(grep '^GAMA_HARNESS_TOKEN=' /etc/gama-harness.env | cut -d= -f2-)
curl -s -X POST http://127.0.0.1:7125/mcp/call \
  -H "X-Token: $TOKEN" -H 'Content-Type: application/json' \
  -d '{"name":"shell","arguments":{"cmd":"echo SIGIL-MCP-LIVE"}}'
```

Response (trimmed):

```json
{"ok":true,"result":{"ok":true,"out":"SIGIL-MCP-LIVE\n",
 "_gtl_receipt":{"seq":807,"signed":true,"key_id":"b04f903a64d346df"},
 "_sigil":{"receipt_id":"8f459a6d-...","verified":true}}}
```

The in-process denial test with a dead gate also returned
`{"ok":false,"blocked":"sigil"}` and did not execute the command.
