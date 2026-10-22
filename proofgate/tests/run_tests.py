#!/usr/bin/env python3
"""Dependency-free test suite for proofgate (no pytest needed)."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import proofgate as pg  # noqa: E402

CASES = []


def test(fn):
    CASES.append(fn)
    return fn


@test
def demo_shape():
    r = pg.demo()
    assert r["counts"] == {"confirmed": 10, "refuted": 2, "unverified": 0}, r["counts"]
    assert r["status"] == "refuted" and r["ok"] is False
    assert len(r["evidence_sha256"]) == 64


@test
def fail_closed_missing_observed():
    assert pg.evaluate({"predicate": "eq_num", "expected": 1})["status"] == "unverified"


@test
def fail_closed_missing_expected():
    assert pg.evaluate({"predicate": "eq_num", "observed": 1})["status"] == "unverified"


@test
def fail_closed_unknown_predicate():
    assert pg.evaluate({"predicate": "vibes", "observed": 1, "expected": 1})["status"] == "unverified"


@test
def fail_closed_nan():
    assert pg.evaluate({"predicate": "eq_num", "observed": "NaN", "expected": 1})["status"] == "unverified"


@test
def bool_is_not_number():
    assert pg.evaluate({"predicate": "eq_num", "observed": True, "expected": 1})["status"] == "unverified"


@test
def numeric_tolerance():
    assert pg.evaluate({"predicate": "eq_num", "observed": "246,50", "expected": 246.5})["status"] == "confirmed"
    assert pg.evaluate({"predicate": "eq_num", "observed": 1, "expected": 1.001})["status"] == "refuted"


@test
def string_normalization():
    assert pg.evaluate({"predicate": "eq_str", "observed": "  A   B ", "expected": "a b"})["status"] == "confirmed"


@test
def hash_semantics():
    assert pg.evaluate({"predicate": "hash_eq", "observed": "abc", "expected": "abc"})["status"] == "confirmed"
    assert pg.evaluate({"predicate": "hash_eq", "observed": "abc", "expected": "abd"})["status"] == "refuted"


@test
def rc_zero():
    assert pg.evaluate({"predicate": "rc_zero", "observed": 0})["status"] == "confirmed"
    assert pg.evaluate({"predicate": "rc_zero", "observed": 1})["status"] == "refuted"


@test
def json_subset():
    assert pg.evaluate({"predicate": "json_field_eq", "observed": {"a": {"b": 2}, "c": 3},
                        "expected": {"a": {"b": 2}}})["status"] == "confirmed"
    assert pg.evaluate({"predicate": "json_field_eq", "observed": {"a": 1},
                        "expected": {"b": 2}})["status"] == "refuted"


@test
def aggregation_precedence():
    claims = [{"predicate": "eq_num", "observed": 1, "expected": 1},
              {"predicate": "eq_num", "observed": None, "expected": 1}]
    assert pg.check(claims)["status"] == "unverified"
    claims.append({"predicate": "eq_num", "observed": 1, "expected": 2})
    assert pg.check(claims)["status"] == "refuted"


@test
def empty_is_unverified():
    assert pg.check([])["status"] == "unverified"


@test
def tamper_detection():
    report = pg.check([{"predicate": "eq_num", "observed": 2, "expected": 2}])
    assert pg.verify(report)["ok"] is True
    report["claims"][0]["observed"] = 3
    v = pg.verify(report)
    assert v["ok"] is False and v["tampered"] is True


@test
def tamper_on_emit():
    report = pg.check([{"predicate": "eq_num", "observed": 2, "expected": 2}])
    bad = pg.check([{"predicate": "eq_num", "observed": 3, "expected": 2}],
                   reported_hash=report["evidence_sha256"])
    assert bad["tampered"] is True and bad["status"] == "unverified"


@test
def canonical_hash_stable():
    a = pg.check([{"predicate": "eq_str", "observed": "x", "expected": "x"}])
    b = pg.check([{"predicate": "eq_str", "observed": "x", "expected": "x"}])
    assert a["evidence_sha256"] == b["evidence_sha256"]


def main():
    failed = 0
    for fn in CASES:
        try:
            fn()
            print("PASS", fn.__name__)
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print("FAIL", fn.__name__, "->", exc)
    print("\n%d/%d passed" % (len(CASES) - failed, len(CASES)))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
