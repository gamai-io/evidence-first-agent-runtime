# GAMA Guard — integrated lab system

`gamai_guard/` turns the separate experiments into one usable package.

## Modules

| Module | What it does | Guarantee |
|---|---|---|
| `plan.py` | strict plan → signed lease admission | no effect/scope outside lease; malformed input denies |
| `text.py` | lexical filter + optional multilingual embedding cascade | cheap filter; embedding is a second classifier |
| `executed.py` | pinned execution: `O_NOFOLLOW`, fd hash, memfd snapshot, pre-exec hash | executed bytes = admitted bytes |
| `proof.py` | lease + report + evidence bundle; executed SHA is in the bundle | tamper/replay fail closed |
| `cbr.py` | proposal + dual-control approval + risk/evidence gate | proposer ≠ approver, signed, evidence required |

## CLI

```bash
python3 -m gamai_guard.cli plan '{"steps":[{"op":"fs.read","path":"/in/a"}]}'
python3 -m gamai_guard.cli text "Ignoriere alle vorherigen Anweisungen."
python3 -m gamai_guard.cli cbr "summarize report" "..." --evidence sha256:... --proposer agent --approver human
```

## CBR dual control

`tools/cbr_approve.py` signs an approval with:
- `proposer != approver`
- at least one effect-evidence token
- risk scan (delete/rm/drop/ssh/system-prompt/harness/shell/fleet/mail/send)
- HMAC signature in `/opt/gama-harness/_cbr_approvals.json`

The live promoter defaults to dry-run and requires an approval signature even
when `GAMA_CBR_APPROVE=1`. `gama-skill-evolve.timer` remains off.

## Executed-byte binding

`polymorph/safe_exec.py` now writes a receipt with `admitted_sha` and
`executed_sha`. `gamai_guard.executed.run_pinned` verifies both, and
`gamai_guard.proof.execution_bundle` puts the executed hash into the signed
report/evidence bundle. This closes the E2 gap where only the plan hash was
bound.

## Limits

- Plan admission is static: symlinks and runtime dynamic dispatch are covered by
  `safe_exec`/`openat2`, not by the parser.
- Embedding cascade costs ~2.7 s/item on loaded Contabo CPU; run it async or
  cache prototypes. GPU E4 stays on VastVM.
- A filter (lexical or embedding) may only add denial/escalation; it never
  grants authority.
