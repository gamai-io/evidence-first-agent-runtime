# Provenance: integrity is not authenticity

`proofgate` binds a report to SHA-256. That answers one question:

> Did this report change after it was emitted?

It does **not** answer:

> Who produced it, and was that producer trustworthy?

A hash is public and unkeyed. Anyone can recompute it for a forged report. To
make provenance a real claim, sign the report with a key.

## HMAC-SHA256 (stdlib, shared secret)

Use when the producer and verifier are in the same trust domain (one company,
one deployment, one node fleet) and can share a secret.

```python
import sys
sys.path.insert(0, "proofgate")
import proofgate
import provenance

report = proofgate.demo()
signed = provenance.sign_hmac(report, "shared-secret", key_id="node-a")
assert provenance.verify_hmac(signed, "shared-secret")["ok"]
assert not provenance.verify_hmac(signed, "wrong-secret")["ok"]

# The evidence hash is still valid after signing.
assert proofgate.verify(signed)["ok"]
```

Properties:

- constant-time comparison;
- `key_id` is carried in the envelope so keys can rotate;
- changing any field (claims, counts, timestamp, evidence hash) invalidates the
  signature;
- the `signature` field itself is excluded from the signed payload.

Limitation: every verifier that can check the signature can also forge it. Use
per-node secrets, keep them out of the repo, and rotate them.

## Ed25519 (optional `cryptography`)

Use when verifiers should be able to check a signature without holding a
signing secret.

```python
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding, PrivateFormat, PublicFormat, NoEncryption,
)
import provenance

key = Ed25519PrivateKey.generate()
private_pem = key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
public_pem = key.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)

signed = provenance.sign_ed25519(report, private_pem, key_id="release-2026-10")
assert provenance.verify_ed25519(signed, public_pem)["ok"]
```

Install the optional dependency:

```bash
python -m pip install cryptography
```

Properties:

- the private key signs; the public key verifies;
- a compromised verifier cannot forge new reports;
- `key_id` supports rotation and revocation lists.

Limitation: a compromised **producer** can sign a false report. The signature
proves the report came from the holder of that key, not that the evidence was
true.

## What neither scheme proves

1. **Source truthfulness.** A node can observe the wrong thing, or lie, and
   sign the lie.
2. **Freshness.** A valid old report can be replayed unless you bind a nonce,
   timestamp and verifier challenge.
3. **Execution integrity.** A compromised process can sign whatever it wants.
4. **Key custody.** If the private key or HMAC secret leaks, provenance is
   lost.

For stronger claims, combine signatures with:

- a per-node key stored outside the application directory;
- a monotonic counter or nonce in the signed payload;
- independent witnesses (a second node countersigns the same evidence);
- trusted execution/attestation (TPM, secure enclave, measured boot);
- retention of the raw evidence next to the signed report.

## Tests

```bash
python3 proofgate/tests/test_provenance.py
```

The tests cover: valid HMAC, wrong key, tamper detection, evidence-hash
survival, valid Ed25519, and Ed25519 tamper detection (skipped when
`cryptography` is absent).
