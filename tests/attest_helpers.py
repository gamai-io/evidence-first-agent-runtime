"""HMAC claim attestation used by the claim-source test.

This is the narrow piece of the former vendored ``proofgate/`` copy that
upstream ``proofgate-runtime`` does not provide. It stays in ``tests/`` so the
trusted-source rule is still exercised without re-vendoring the whole package.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

from proofgate_runtime import check


def _canon(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), default=str)


def attest_claims(claims: list[dict], *, key: str | bytes, source: str) -> list[dict]:
    """Sign claim bodies for a named source (HMAC-SHA256)."""
    if isinstance(key, str):
        key = key.encode("utf-8")
    if not key:
        raise ValueError("attestation key must not be empty")
    out = []
    for claim in claims:
        signed_claim = {**claim, "source": source}
        body = _canon({k: v for k, v in signed_claim.items() if k != "attestation"})
        sig = hmac.new(key, body.encode("utf-8"), hashlib.sha256).hexdigest()
        out.append({**signed_claim,
                    "attestation": {"alg": "HMAC-SHA256", "value": sig}})
    return out


def check_attested(claims: list[dict], *, key: str | bytes, source: str,
                   trusted_sources: tuple[str, ...] = ("executor", "sor")) -> dict:
    """Evaluate only claims attested by a trusted, non-model source."""
    if source not in trusted_sources:
        return {"ok": False, "status": "unverified",
                "reason": "untrusted evidence source: %s" % source,
                "claims": [], "counts": {"confirmed": 0, "refuted": 0, "unverified": 0}}
    if isinstance(key, str):
        key = key.encode("utf-8")
    checked = []
    for claim in claims:
        cs = claim.get("source")
        if cs is not None and (cs not in trusted_sources or cs != source):
            return {"ok": False, "status": "unverified",
                    "reason": "claim source not trusted/mismatched: %s" % cs,
                    "claims": [], "counts": {"confirmed": 0, "refuted": 0, "unverified": 0}}
        sig = (claim.get("attestation") or {}).get("value")
        body = _canon({k: v for k, v in claim.items() if k != "attestation"})
        expected = hmac.new(key, body.encode("utf-8"), hashlib.sha256).hexdigest()
        if not sig or not hmac.compare_digest(str(sig), expected):
            return {"ok": False, "status": "unverified",
                    "reason": "claim attestation missing or invalid",
                    "claims": [], "counts": {"confirmed": 0, "refuted": 0, "unverified": 0}}
        checked.append(claim)
    return check(checked)
