#!/usr/bin/env python3
"""Provenance signatures for proofgate reports.

SHA-256 answers "did this report change?" It does NOT answer "who produced it?"
or "was the producer trustworthy?". This module adds an explicit envelope:

- HMAC-SHA256: symmetric authenticity. Producer and verifier share a secret.
  Cheap, stdlib-only, good for a single trust domain.
- Ed25519: asymmetric authenticity. Producer signs with a private key; anyone
  with the public key verifies. Requires the optional ``cryptography`` package.

Neither proves that the evidence was truthful at the source. A compromised node
can sign a false claim. Trusted execution/attestation is a separate problem.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any


def _canon(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), default=str).encode("utf-8")


def _signed_bytes(report: dict) -> bytes:
    # The evidence hash is part of what gets signed; the signature is not.
    return _canon({k: v for k, v in report.items() if k != "signature"})


def sign_hmac(report: dict, key: str | bytes, key_id: str = "default") -> dict:
    """Return a copy of the report with an HMAC-SHA256 signature envelope."""
    if isinstance(key, str):
        key = key.encode("utf-8")
    if not key:
        raise ValueError("key must not be empty")
    digest = hmac.new(key, _signed_bytes(report), hashlib.sha256).hexdigest()
    out = dict(report)
    out["signature"] = {
        "alg": "HMAC-SHA256",
        "key_id": key_id,
        "value": digest,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    return out


def verify_hmac(report: dict, key: str | bytes) -> dict:
    """Verify an HMAC envelope. Constant-time compare; never raises."""
    if isinstance(key, str):
        key = key.encode("utf-8")
    sig = report.get("signature") or {}
    if sig.get("alg") != "HMAC-SHA256":
        return {"ok": False, "reason": "not an HMAC-SHA256 signature"}
    expected = hmac.new(key, _signed_bytes(report), hashlib.sha256).hexdigest()
    ok = hmac.compare_digest(expected, str(sig.get("value", "")))
    return {"ok": ok, "alg": "HMAC-SHA256", "key_id": sig.get("key_id"),
            "expected": expected, "reported": sig.get("value"),
            "tampered": not ok}


def sign_ed25519(report: dict, private_key_pem: bytes, key_id: str = "ed25519") -> dict:
    """Sign with an Ed25519 private key (requires ``cryptography``)."""
    try:
        from cryptography.hazmat.primitives.serialization import load_pem_private_key
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("Ed25519 requires: pip install cryptography") from exc
    key = load_pem_private_key(private_key_pem, password=None)
    signature = key.sign(_signed_bytes(report))
    out = dict(report)
    out["signature"] = {
        "alg": "Ed25519",
        "key_id": key_id,
        "value": base64.b64encode(signature).decode("ascii"),
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    return out


def verify_ed25519(report: dict, public_key_pem: bytes) -> dict:
    """Verify an Ed25519 envelope. Requires ``cryptography``."""
    try:
        from cryptography.hazmat.primitives.serialization import load_pem_public_key
        from cryptography.exceptions import InvalidSignature
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("Ed25519 requires: pip install cryptography") from exc
    sig = report.get("signature") or {}
    if sig.get("alg") != "Ed25519":
        return {"ok": False, "reason": "not an Ed25519 signature"}
    try:
        key = load_pem_public_key(public_key_pem)
        key.verify(base64.b64decode(str(sig.get("value", ""))), _signed_bytes(report))
        ok = True
        reason = "signature valid"
    except (InvalidSignature, ValueError, TypeError) as exc:
        ok = False
        reason = "signature invalid: %s" % exc
    return {"ok": ok, "alg": "Ed25519", "key_id": sig.get("key_id"),
            "reason": reason}


__all__ = ["sign_hmac", "verify_hmac", "sign_ed25519", "verify_ed25519"]
