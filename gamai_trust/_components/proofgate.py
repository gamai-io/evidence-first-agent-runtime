#!/usr/bin/env python3
"""proofgate — fail-closed evidence gate for agent claims.

An agent should not be allowed to say "done" without evidence. proofgate takes
claims (observed vs expected under a predicate), returns confirmed / refuted /
unverified per claim, and binds the whole report to a SHA-256 evidence hash.

Design rules
------------
- fail-closed: missing or malformed evidence is `unverified`, never `confirmed`
- refuted wins over unverified, unverified wins over confirmed
- tamper-evident: recompute the hash and compare; mismatch invalidates report
- zero dependencies; deterministic canonical JSON

Statuses
--------
confirmed : evidence present and predicate holds
refuted   : evidence present and predicate does NOT hold
unverified: evidence missing/malformed, or unknown predicate
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from decimal import Decimal, InvalidOperation
from typing import Any

PREDICATES = (
    "eq_num",
    "eq_str",
    "hash_eq",
    "rc_zero",
    "contains",
    "json_field_eq",
)
HEX_RE = re.compile(r"^[0-9a-fA-F]{32,128}$")
NUM_TOL = Decimal("1e-9")


class EvidenceError(ValueError):
    """Raised when evidence is structurally unusable."""


def _canon(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), default=str)


def sha256_text(text: Any) -> str:
    return hashlib.sha256(str(text).encode("utf-8", "replace")).hexdigest()


def evidence_hash(payload: Any) -> str:
    """Hash of the canonical payload, excluding the hash field itself."""
    if isinstance(payload, dict):
        # signature is an envelope field, not part of the evidence payload
        payload = {k: v for k, v in payload.items()
                   if k not in ("evidence_sha256", "signature")}
    return sha256_text(_canon(payload))


def _is_number(value: Any) -> bool:
    if isinstance(value, bool) or value is None:
        return False
    if isinstance(value, (int, float, Decimal)):
        return True
    if isinstance(value, str):
        try:
            Decimal(value.strip().replace(",", "."))
            return True
        except (InvalidOperation, AttributeError):
            return False
    return False


def _to_decimal(value: Any) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise EvidenceError("not a number")
    text = str(value).strip().replace(",", ".")
    try:
        return Decimal(text)
    except InvalidOperation as exc:
        raise EvidenceError("not a number: %r" % (value,)) from exc


def _norm_str(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value)).strip()


def _missing(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip()) \
        or (isinstance(value, (list, dict, tuple, set)) and len(value) == 0)


def _subset(expected: Any, observed: Any) -> bool:
    """Recursive subset check for dicts; equality for everything else."""
    if isinstance(expected, dict):
        if not isinstance(observed, dict):
            return False
        return all(k in observed and _subset(v, observed[k])
                   for k, v in expected.items())
    if isinstance(expected, list):
        return observed == expected
    return expected == observed


def evaluate(claim: dict) -> dict:
    """Evaluate one claim. Never raises; returns a status dict."""
    if not isinstance(claim, dict):
        return {"status": "unverified", "reason": "claim is not an object"}

    text = claim.get("text", "")
    predicate = claim.get("predicate")
    observed = claim.get("observed")
    expected = claim.get("expected")

    out = {
        "text": text,
        "predicate": predicate,
        "observed": observed,
        "expected": expected,
    }

    if predicate not in PREDICATES:
        out.update(status="unverified", reason="unknown predicate")
        return out
    if _missing(observed):
        out.update(status="unverified", reason="missing observed evidence")
        return out
    if predicate != "rc_zero" and expected is None:
        out.update(status="unverified", reason="missing expected value")
        return out

    try:
        if predicate == "eq_num":
            ok = abs(_to_decimal(observed) - _to_decimal(expected)) <= NUM_TOL
        elif predicate == "eq_str":
            ok = _norm_str(observed).casefold() == _norm_str(expected).casefold()
        elif predicate == "hash_eq":
            obs = str(observed).strip()
            exp = str(expected).strip()
            if HEX_RE.match(obs) and HEX_RE.match(exp):
                ok = obs.lower() == exp.lower()
            else:
                ok = sha256_text(obs) == sha256_text(exp)
        elif predicate == "rc_zero":
            ok = int(observed) == 0
        elif predicate == "contains":
            if _missing(expected):
                raise EvidenceError("empty expected substring")
            ok = str(expected).casefold() in str(observed).casefold()
        elif predicate == "json_field_eq":
            if not isinstance(expected, dict):
                raise EvidenceError("json_field_eq expects a dict")
            ok = _subset(expected, observed)
        else:  # pragma: no cover - guarded above
            ok = False
    except (EvidenceError, InvalidOperation, TypeError, ValueError) as exc:
        out.update(status="unverified", reason="malformed evidence: %s" % exc)
        return out

    out["status"] = "confirmed" if ok else "refuted"
    out["reason"] = "predicate holds" if ok else "predicate mismatch"
    return out


def check(claims: list[dict], *, reported_hash: str | None = None) -> dict:
    """Evaluate a batch of claims and return an evidence-bound report."""
    if not isinstance(claims, list):
        claims = []
    results = [evaluate(c) for c in claims]

    if any(r["status"] == "refuted" for r in results):
        status = "refuted"
    elif any(r["status"] == "unverified" for r in results) or not results:
        status = "unverified"
    else:
        status = "confirmed"

    report = {
        "ok": status == "confirmed",
        "status": status,
        "claims": results,
        "counts": {
            s: sum(1 for r in results if r["status"] == s)
            for s in ("confirmed", "refuted", "unverified")
        },
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    digest = evidence_hash(report)
    report["evidence_sha256"] = digest
    if reported_hash is not None and reported_hash != digest:
        report["tampered"] = True
        report["ok"] = False
        report["status"] = "unverified"
        report["reason"] = "evidence hash mismatch (tampered or stale)"
    return report


def verify(report: dict) -> dict:
    """Recompute and verify a previously emitted report."""
    reported = report.get("evidence_sha256")
    expected = evidence_hash(report)
    ok = bool(reported) and reported == expected
    return {"ok": ok, "expected": expected, "reported": reported,
            "tampered": not ok}


# --------------------------------------------------------------------- demo
def demo() -> dict:
    """12 deterministic claims: 10 confirmed, 2 refuted, 0 unverified.

    All evidence is local and reproducible; no network or database required.
    """
    payload = "EVIDENCE-DEMO"
    digest = sha256_text(payload)
    rc_ok = 0
    rc_bad = 2
    claims = [
        {"text": "2 + 2 = 4", "observed": 4, "expected": 4, "predicate": "eq_num"},
        {"text": "17% of 1450 = 246.5", "observed": "246.50", "expected": 246.5,
         "predicate": "eq_num"},
        {"text": "normalized name matches", "observed": "  Alpha   Beta ",
         "expected": "alpha beta", "predicate": "eq_str"},
        {"text": "payload digest matches", "observed": digest,
         "expected": digest, "predicate": "hash_eq"},
        {"text": "command exited 0", "observed": rc_ok, "expected": 0,
         "predicate": "rc_zero"},
        {"text": "stdout contains OK", "observed": "build: OK (3 files)",
         "expected": "ok", "predicate": "contains"},
        {"text": "JSON field status=ok", "observed": {"status": "ok", "n": 3},
         "expected": {"status": "ok"}, "predicate": "json_field_eq"},
        {"text": "nested JSON field holds", "observed": {"a": {"b": 2}, "c": 1},
         "expected": {"a": {"b": 2}}, "predicate": "json_field_eq"},
        {"text": "tuple count on stdout", "observed": "count=1115",
         "expected": "1115", "predicate": "contains"},
        {"text": "rc equality for a non-zero failure", "observed": rc_bad,
         "expected": 2, "predicate": "eq_num"},
        # intentionally false claims -> refuted
        {"text": "FALSE: 2 + 2 = 5", "observed": 4, "expected": 5, "predicate": "eq_num"},
        {"text": "FALSE: command exited 0", "observed": rc_bad, "expected": 0,
         "predicate": "rc_zero"},
    ]
    return check(claims)


def _read_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__.strip())
        return 2
    cmd = argv[1]
    if cmd == "demo":
        report = demo()
        print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
        return 0 if report["counts"]["refuted"] == 2 else 1
    if cmd == "check":
        if len(argv) < 3:
            print("usage: proofgate.py check claims.json", file=sys.stderr)
            return 2
        data = _read_json(argv[2])
        claims = data.get("claims") if isinstance(data, dict) else data
        report = check(claims or [], reported_hash=(data or {}).get("evidence_sha256")
                       if isinstance(data, dict) else None)
        print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
        return 0 if report["ok"] else 1
    if cmd == "verify":
        if len(argv) < 3:
            print("usage: proofgate.py verify report.json", file=sys.stderr)
            return 2
        print(json.dumps(verify(_read_json(argv[2])), ensure_ascii=False, indent=2))
        return 0
    print("unknown command: %s" % cmd, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
