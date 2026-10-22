#!/usr/bin/env python3
"""Tests for proofgate provenance envelopes (stdlib HMAC, optional Ed25519)."""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import proofgate  # noqa: E402
import provenance  # noqa: E402

checks = []


def ok(name: str, cond: bool, detail: str = "") -> None:
    checks.append({"name": name, "ok": bool(cond), "detail": detail})


report = proofgate.demo()
ok("demo report verifies", proofgate.verify(report)["ok"])
ok("demo status refuted", report["status"] == "refuted")

signed = provenance.sign_hmac(report, "test-key", "unit")
ok("hmac signature present", signed["signature"]["alg"] == "HMAC-SHA256")
ok("hmac verifies", provenance.verify_hmac(signed, "test-key")["ok"])
ok("hmac wrong key fails", not provenance.verify_hmac(signed, "wrong-key")["ok"])
ok("evidence hash survives signing", proofgate.verify(signed)["ok"])

tampered = dict(signed)
tampered["claims"] = [dict(c) for c in signed["claims"]]
tampered["claims"][0]["text"] = "tampered"
ok("hmac detects tamper", not provenance.verify_hmac(tampered, "test-key")["ok"])

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.serialization import (
        Encoding, PrivateFormat, PublicFormat, NoEncryption,
    )
    key = Ed25519PrivateKey.generate()
    priv = key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
    pub = key.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
    esigned = provenance.sign_ed25519(report, priv)
    ok("ed25519 verifies", provenance.verify_ed25519(esigned, pub)["ok"])
    etampered = dict(esigned)
    etampered["status"] = "confirmed"
    ok("ed25519 detects tamper", not provenance.verify_ed25519(etampered, pub)["ok"])
except ImportError:
    ok("ed25519 optional dependency absent (skipped)", True, "install cryptography to test")

passed = sum(1 for c in checks if c["ok"])
for c in checks:
    print(("PASS " if c["ok"] else "FAIL ") + c["name"] + (
        " — " + c["detail"] if c["detail"] else ""))
print("%d/%d passed" % (passed, len(checks)))
raise SystemExit(0 if passed == len(checks) else 1)
