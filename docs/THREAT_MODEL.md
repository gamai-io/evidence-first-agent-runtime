# Threat model (trust layer)

Scope: `proofgate`, `agent-immunity`, `crossnode-bench`, the CLI, and the MCP
server. The model, the host harness, and the signing key custody are outside
this repository.

## Assets

- Evidence reports and their SHA-256 hashes.
- Provenance signatures (HMAC secret or Ed25519 private key).
- Antibody database (which attacks were seen and blocked).
- Benchmark results and ground-truth records.
- The integrity of the decision: allow vs block, confirmed vs refuted.

## Adversaries

- A compromised or hallucinating model that emits false claims.
- A malicious tool/document that injects instructions.
- A compromised node that reports `ok:true` while ground truth fails.
- A replay attacker who reuses an old valid report.
- A key thief who obtains the HMAC secret or private key.
- A supply-chain attacker in a dependency or CI action.

## STRIDE

| Threat | Example | Mitigation | Residual risk |
|---|---|---|---|
| **Spoofing** | Forged report claims to be from node A | HMAC or Ed25519 signature with `key_id`; verifier pins the public key | A compromised producer can sign a false report |
| **Tampering** | Change `observed` or `status` after emission | SHA-256 over canonical report; signature covers the hash; `verify` returns `tampered` | None for the report itself; evidence source may still be wrong |
| **Repudiation** | Producer denies emitting a report | Signature + timestamp + `key_id`; optional external log | No trusted timestamp by default; add RFC 3161 or a witness |
| **Information disclosure** | Logs or MCP output leak secrets | Do not log evidence bodies; redact in callers; MCP is local stdio | Caller can still put secrets in `observed` |
| **Denial of service** | Huge claim list or pathological JSON | Caller-side limits; `MAX_*` bounds in agent-immunity; no network listener | No hard CPU/memory quota in the library |
| **Elevation of privilege** | MCP tool abused to write files or run shell | MCP tools are pure/read-only: verify, check, add antibody, stats, demo | Host that wraps the MCP server must enforce its own permissions |
| **Prompt injection** | Document says "ignore previous instructions" | NFKC + invisible stripping + homoglyph folding + base64 + patterns + antibodies | Adaptive attacker with new vocabulary; held-out zero-shot is 29% |
| **False success** | Node says `ok:true` after a timeout | Ground-truth predicates in crossnode-bench; false success is a separate metric | Benchmark tasks are finite; a new failure mode can be missed |
| **Key compromise** | HMAC secret or private key leaks | Keys outside repo; rotation via `key_id`; least privilege | Rotation/revocation is operational, not enforced by the library |
| **Supply chain** | Malicious pip package or CI action | Core has no runtime dependencies; CI actions pinned by major version; add SBOM and secret scanning | `cryptography` is optional and must be pinned by the consumer |

## Trust boundaries and assumptions

1. `observed` evidence is supplied by the caller. If the caller passes model
   output as evidence, the gate is defeated.
2. `proofgate` checks a predicate, not semantic truth. "The customer is happy"
   must be decomposed into measurable observations.
3. `agent-immunity` is lexical and pattern-based. It is a memory layer, not a
   semantic classifier.
4. `crossnode-bench` trusts its ground-truth predicates. A wrong predicate
   produces a wrong verdict.
5. The MCP server assumes a local/trusted transport. Do not expose it on a
   public interface without authentication and authorization.

## Out of scope

- Model weights, inference safety, and jailbreaks unrelated to these
  components.
- Host-level sandboxing and OS permissions.
- Physical access to the signing key.
- Legal compliance of the caller's data processing.

## Minimum controls before a production deployment

- Sign reports with a per-node key stored outside the repo.
- Pin the verifier's public key and reject unknown `key_id`.
- Keep the antibody DB private; it reveals which attacks were seen.
- Run the MCP server over stdio or a private authenticated channel.
- Measure false positives and false successes on your own traffic.
- Get an independent review before making a trust claim to a customer.
