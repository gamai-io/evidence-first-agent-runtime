# Skill-evolve: review-only timer + signed approval

The old `gama-skill-evolve.service` ran `gama_learn.py promote --min 5`, which
could deploy auto-skills without CBR dual-control. It is now **review-only**.

## State
- `gama-skill-evolve.timer`: **active**, next run ~04:30 (+ jitter).
- `gama-skill-evolve.service`: runs `skill_evolve_review.py --min 5`.
- Review file: `/opt/gama-harness/_skill_evolve_review.jsonl`.
- Latest run: **8 reviewed, 0 deployed**; live manifest unchanged (49 skills).
- Backup units: `*.bak_review_20261023`.

## Approval flow
1. Review a record: name, sha, gate result, goal.
2. Sign exactly that name + sha:
   ```bash
   python3 /root/gamaos/skill_evolve_approve.py \
     --name gama-auto-... --sha <64hex> --proposer agent --approver human
   ```
   Creates `/opt/gama-harness/.skill_evolve_approval_key` (0600) and
   `_skill_evolve_approvals.json` (0600), HMAC-signed.
3. Apply only approved records:
   ```bash
   python3 /root/gamaos/skill_evolve_review.py --min 5 --apply-approved
   ```
   Rejects if proposer==approver, sha differs, or the signature does not verify.

## Limits
- Approval is content-bound: if cases change, the sha changes and the approval
  is stale.
- `--apply-approved` still runs `gama_skill_evolve.deploy()` (stage, gate,
  backup, atomic replace, synthetic gate, audit).
- No key material is printed; key custody remains with root.
