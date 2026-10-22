# Security alert — CBR auto-promotion stopped (2026-10-22)

A read-only review of the local CBR store found a persistence risk.

## Finding

- `/root/gamacode/cases.db`: **833 cases**, **131** qualify for promotion
  (`ok>=3`, `fail<=1`), **120** were still unpromoted.
- Nightly timers:
  - `gama-cbr-promote.timer` 03:40
  - `gama-skill-evolve.timer` 04:30
- A known contaminated row: goal `obrisi /var/log sve`, `ok=13`, tool
  `fleet_status`; the action was blocked but counted as completion.
- Queued rows include system-prompt exfiltration and harness-overwrite goals.
- `gama_cbr_promote.py` promotes by `intent` (short bag of words) and writes to
  shared memory; the memory sync then spreads it fleet-wide.
- `antibody_add` has no dual control and re-add resets decay.

## Action taken

Stopped both timers; **no data was deleted or modified**. The CBR script is now
quarantine-first (see `docs/CBR_GATE_2026-10-22.md`), and the CBR timer is active
in dry-run with **0 promotions / 58 review**. `gama-skill-evolve.timer` remains
inactive until review.

```bash
systemctl stop gama-cbr-promote.timer
systemctl stop gama-skill-evolve.timer
```

Both are inactive. Do not restart until the promotion gate has:

- effect/evidence proof, not just `ok` count
- proposer != approver (dual control)
- TTL, scope and revocation
- quarantine of `intent` collisions and destructive goals
- a human review for irreversible/tool-writing recipes.

Re-enable manually only after review:

```bash
systemctl start gama-cbr-promote.timer
systemctl start gama-skill-evolve.timer
```
