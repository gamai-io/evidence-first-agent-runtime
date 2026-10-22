# Polymorph E1 — capability widening

Defensive prototype. It does **not** generate malware and does **not** execute
the corpus. It tests one property:

> A semantics-preserving or malicious variant may change syntax, but it may not
> gain a capability outside the signed lease.

## Run

```bash
python3 polymorph/gen_e1.py
python3 polymorph/run_e1.py
python3 polymorph/tests/run_tests.py
```

## Corpus

- 20 benign plans inside the lease (`/in` read, `/out` write, approved
  `api.internal`, `/bin/true`, `/bin/echo`, mail/chat).
- 40 malicious plans that add external network, shell exec, `/etc/passwd`,
  `/root/.ssh`, path escape, external send or external DB.

Expected: **20/20 benign allowed, 40/40 malicious denied, 40/40 with a recorded
capability gain, 0 false allow, 0 false deny**, static check p50 under 1 ms.

This is a static admission check, not a sandbox. Execution isolation is a
separate layer (PROTEAN / gVisor / Firecracker). The result does not prove
protection against an adaptive attacker.
