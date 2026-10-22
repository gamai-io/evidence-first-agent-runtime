#!/usr/bin/env python3
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from effect_lease import Lease, check, loads_strict  # noqa: E402

L = Lease.from_dict({"effects": {
    "fs.read": ["/in"], "fs.write": ["/out"],
    "net.connect": ["api.internal"], "exec": ["/bin/true"],
    "db.read": ["/in/cache.db"], "send": ["mail"],
}})
CASES = []


def test(fn):
    CASES.append(fn)
    return fn


@test
def benign_allows():
    assert check({"id": "b", "steps": [
        {"op": "fs.read", "path": "/in/a"},
        {"op": "fs.write", "path": "/out/a"},
    ]}, L)["allow"]


@test
def net_external_denied():
    d = check({"id": "m", "steps": [{"op": "net.connect", "host": "evil.example"}]}, L)
    assert not d["allow"] and d["capability_gain"] == ["net.connect"]


@test
def exec_shell_denied():
    assert not check({"id": "m", "steps": [{"op": "exec", "target": "/bin/sh"}]}, L)["allow"]


@test
def path_escape_denied():
    assert not check({"id": "m", "steps": [{"op": "fs.write", "path": "/out/../etc/x"}]}, L)["allow"]


@test
def read_etc_denied():
    assert not check({"id": "m", "steps": [{"op": "fs.read", "path": "/etc/passwd"}]}, L)["allow"]


@test
def approved_net_allowed():
    assert check({"id": "b", "steps": [{"op": "net.connect", "host": "api.internal"}]}, L)["allow"]


@test
def missing_steps_denied():
    assert not check({"id": "m", "ops": []}, L)["allow"]


@test
def missing_scope_denied():
    assert not check({"id": "m", "steps": [{"op": "fs.read"}]}, L)["allow"]


@test
def nested_args_denied():
    assert not check({"id": "m", "steps": [{"op": "fs.read", "args": {"path": "/etc/passwd"}}]}, L)["allow"]


@test
def extra_key_denied():
    assert not check({"id": "m", "steps": [{"op": "fs.read", "path": "/in/a", "url": "https://x"}]}, L)["allow"]


@test
def percent_traversal_denied():
    assert not check({"id": "m", "steps": [{"op": "fs.read", "path": "/in/%2e%2e/%2e%2e/etc/passwd"}]}, L)["allow"]


@test
def fullwidth_traversal_denied():
    assert not check({"id": "m", "steps": [{"op": "fs.read", "path": "/in/／..／..／etc/passwd"}]}, L)["allow"]


@test
def malformed_is_deny_not_exception():
    d = check({"id": "m", "steps": [{"op": "gpu.run"}]}, L)
    assert d["allow"] is False and d["reasons"][0].startswith("schema:")


@test
def duplicate_keys_rejected():
    try:
        loads_strict('{"a":1,"a":2}')
    except ValueError:
        return
    raise AssertionError("duplicate key accepted")


@test
def unknown_effect_denied():
    assert not check({"id": "m", "steps": [{"op": "gpu.run"}]}, L)["allow"]


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
