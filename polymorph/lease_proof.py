"""Lease-bound proof bundle (E2 prototype).

Binds a PROTEAN-style lease, a proofgate-style report and an evidence record
into one HMAC-signed bundle. It is deliberately stdlib-only and does not
replace proofgate; it demonstrates the binding and fail-closed checks.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import time


def canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def sha(obj) -> str:
    return hashlib.sha256(canon(obj)).hexdigest()


def sign(bundle: dict, key: bytes) -> str:
    body = {k: bundle[k] for k in ("lease", "report", "evidence")}
    return hmac.new(key, canon(body), hashlib.sha256).hexdigest()


def make_bundle(lease: dict, report: dict, evidence: dict, key: bytes) -> dict:
    bundle = {"lease": lease, "report": report, "evidence": evidence}
    bundle["sig"] = sign(bundle, key)
    return bundle


class Verifier:
    def __init__(self, key: bytes, audience: str = "protean/vastvm"):
        self.key = key
        self.audience = audience
        self.seen: set[str] = set()

    def verify(self, bundle: dict, now: float | None = None) -> dict:
        now = time.time() if now is None else now
        lease = bundle.get("lease") or {}
        report = bundle.get("report") or {}
        evidence = bundle.get("evidence") or {}
        reasons = []

        if not hmac.compare_digest(bundle.get("sig", ""), sign(bundle, self.key)):
            reasons.append("bad_signature")
        if lease.get("audience") != self.audience:
            reasons.append("wrong_audience")
        if float(lease.get("exp", 0)) <= now:
            reasons.append("expired")
        if lease.get("nonce") in self.seen:
            reasons.append("replay")
        if report.get("lease_id") != lease.get("lease_id"):
            reasons.append("lease_id_mismatch")
        if report.get("genome_hash") != lease.get("genome_hash"):
            reasons.append("genome_mismatch")
        if report.get("cmd_sha") != lease.get("cmd_sha"):
            reasons.append("cmd_mismatch")
        if report.get("out_sha") != evidence.get("out_sha"):
            reasons.append("evidence_out_mismatch")
        if report.get("status") not in ("confirmed", "refuted", "unverified"):
            reasons.append("bad_status")

        if reasons:
            return {"ok": False, "allow": False, "reasons": reasons}
        self.seen.add(lease["nonce"])
        return {"ok": True, "allow": True, "reasons": [], "lease_id": lease["lease_id"]}
