# Trust Layer Conformance (draft v0.1)

A **conformant** trust layer makes a verifiable decision about an agent claim and
does not turn missing evidence into success.

This document is a testable contract, not a certification. A result is only a
claim about the tests that were run.

## Required properties

| ID | Requirement | Test |
|---|---|---|
| C1 | **Tri-state decision**: every claim returns `confirmed`, `refuted`, or `unverified`. | Feed one true, one false, and one missing-evidence claim. |
| C2 | **Fail closed**: missing, malformed, or tampered evidence is never `confirmed`. | Remove one field, change one byte, and truncate a record. |
| C3 | **Evidence binding**: the decision is bound to a SHA-256 over canonical claim + evidence. | Verify, mutate the claim, verify again; must be `refuted`/tampered. |
| C4 | **Deterministic replay**: same input and same verifier produce the same decision and hash. | Run 10 times; compare decision and hash. |
| C5 | **No silent success on remote actions**: a remote action is `confirmed` only if its effect is observed. | Timeout and nonexistent target must not return success. |
| C6 | **Refusal memory**: a known injection can be blocked and counted without executing it. | Add payload, re-submit, assert `blocked` and stable count. |
| C7 | **False-success measurement**: the suite reports false-success rate on a held-out set. | Run the benchmark; publish numerator, denominator, and seed. |
| C8 | **Honest limits**: the implementation publishes what it does not cover. | Review `docs/THREAT_MODEL.md` and benchmark limitations. |

## Minimum evidence bundle

- `tasks.json` (inputs, expected outcome, category)
- runner and seed
- result JSON (`confirmed`, `refuted`, `unverified` counts)
- report with method, sample size, and limitations
- SHA-256 for each artifact
- CI run URL and commit

## What conformance does **not** mean

- It does not mean the agent is safe, correct, or secure in general.
- It does not replace an independent security audit.
- It does not cover model behaviour outside the published test set.
- It does not authorize high-impact actions without human policy.

## Reference implementation

`gamai-io/evidence-first-agent-runtime` implements the three components used in
this draft:

- `proofgate/` — claim/evidence gate
- `agent-immunity/` — refusal memory
- `crossnode-bench/` — remote false-success detection

Run `./repro.sh` and compare the published output with your own.

## Versioning

Draft v0.1, October 2026. Breaking changes to C1–C4 require a major version.
Comments and counterexamples are welcome via GitHub issues.
