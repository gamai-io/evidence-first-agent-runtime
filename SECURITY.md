# Security policy

## Scope

This project contains three defensive components. We consider these classes of
report in scope:

- a claim that `proofgate` marks `confirmed` without valid evidence, or a
  mutation that still verifies as intact;
- a prompt injection that bypasses `agent-immunity` after normalization and
  is reproducible on the public corpus, **or** a false denial of clearly
  benign text that is reproducible;
- a false success that `crossnode-bench` fails to detect given a node that
  claims `ok:true` while ground truth fails;
- a provenance envelope (`HMAC-SHA256` or `Ed25519`) that verifies after the
  signed report was mutated, or a signature that does not cover the evidence
  hash.

Out of scope: model-level jailbreaks unrelated to these components, denial of
service by resource exhaustion, reports that require private data, and
compromise of a signing key (HMAC secret or Ed25519 private key). Keys must be
kept outside the repository; a leaked key is a deployment incident, not a
component bypass.

## Reporting

Open a **private** security advisory on the affected repository, or email the
maintainer listed in the repository profile. Include:

1. affected component and version/commit,
2. a minimal reproduction (input + observed + expected),
3. impact and whether it is exploitable without local access.

We aim to acknowledge within 72 hours and to publish a fix + credit (if
desired) within 30 days.

## Safe harbor

Good-faith research on your own deployment, following this policy, is welcome.
Do not test against third-party systems without permission.
