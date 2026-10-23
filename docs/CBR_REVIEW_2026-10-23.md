# CBR review — 2026-10-23 (read-only)

State: `_cbr_review.jsonl` has **58 unique cases**, **0 promotions**.
`gama-cbr-promote.timer` is active in review/dry-run mode. No memory rows were
deleted or promoted.

## Why cases are quarantined

| Reason | Count |
|---|---:|
| `approval_required` | 26 |
| `no_evidence` | 9 |
| `risky_tool:run` | 7 |
| `risky_tool:shell` | 7 |
| `risky_goal` (+ tool) | 5 |
| `risky_tool:fleet_status` | 2 |
| `risky_tool:fs_write` | 1 |
| `risky_tool:hc,run` | 1 |

Most are ordinary-looking intents (`bih glavni grad kratko`, `alfa kupca
nadji`, `zdravo`) that fail the evidence/approval gate. That is the gate
working as designed, not a backlog to auto-approve.

## Skill-evolve decision

`gama-skill-evolve.timer` remains **inactive**. It calls
`gama_learn.py promote --min 5`, which uses `gama_skill_evolve.deploy()`:
staging + static/synthetic gates + backup/rollback/audit, but **no CBR
dual-control**. Enabling it would deploy auto-skills without
`proposer != approver` or a signed approval, so it must stay off until the
service is wrapped by a signed-approval path.

`gama_skill_evolve.py self-test` passes 8/8 (gate/reject/repair/rollback/audit).
`gama_skill_evolve.py propose --min 5 --dry` currently lists 8 candidates and
deploys **0**.

## Commands

```bash
wc -l /opt/gama-harness/_cbr_review.jsonl
systemctl is-active gama-cbr-promote.timer gama-skill-evolve.timer
python3 /root/gamaos/gama_skill_evolve.py self-test
python3 /root/gamaos/gama_skill_evolve.py propose --min 5 --dry
```
