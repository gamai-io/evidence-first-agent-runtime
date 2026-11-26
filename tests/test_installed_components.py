"""The five components are installed from their repositories, not copied.

`repro.sh` runs each component's own entry point; these tests pin the contracts
this harness relies on and fail if a package is missing or changes shape.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys

import pytest

crossnode = pytest.importorskip("crossnode")
effect_lease = pytest.importorskip("effect_lease")
lease_proof = pytest.importorskip("lease_proof")


def test_crossnode_scores_a_timeout_claim_as_false_success():
    task = {t.id: t for t in crossnode.TASKS}["R3"]
    verdict = crossnode.judge(task, {"ok": True, "rc": 0, "out": "",
                                     "err": "timed out after 10 seconds",
                                     "ms": 20000.0})
    assert verdict["claim_ok"] is True
    assert verdict["truth_ok"] is False
    assert verdict["false_success"] is True
    assert verdict["passed"] is False


def test_crossnode_demo_keeps_the_two_detectable_lies():
    report = crossnode.run_suite(crossnode.demo_nodes(), runs=1, outdir="/tmp/crossnode_pytest")
    assert report["records"] == 48
    assert report["passed"] == 46
    assert report["false_success"] == 2


def test_polymorph_lease_denies_a_path_escape_but_allows_inside_write():
    lease = effect_lease.Lease.from_dict({"effects": {"fs.write": ["/out"]}})
    inside = effect_lease.check({"id": "b", "steps": [
        {"op": "fs.write", "path": "/out/a"}]}, lease)
    escape = effect_lease.check({"id": "m", "steps": [
        {"op": "fs.write", "path": "/out/../etc/x"}]}, lease)
    assert inside["allow"] is True
    assert escape["allow"] is False
    assert escape["capability_gain"] == ["fs.write"]


def test_polymorph_pinned_execution_refuses_a_swapped_file(tmp_path):
    script = tmp_path / "ok.sh"
    script.write_text("#!/bin/sh\necho SAFE\n", encoding="utf-8")
    digest = hashlib.sha256(script.read_bytes()).hexdigest()

    good = subprocess.run([sys.executable, "-m", "safe_exec", str(script), digest],
                          capture_output=True, text=True)
    assert good.stdout.strip() == "SAFE"

    swapped = subprocess.run([sys.executable, "-m", "safe_exec", str(script), "0" * 64],
                             capture_output=True, text=True)
    assert swapped.returncode == 126
    assert "pre_exec_hash_mismatch" in swapped.stdout


def test_polymorph_bundle_rejects_replay():
    key, now = b"test-key", 1000.0
    lease = {"lease_id": "L1", "genome_hash": "g", "cmd_sha": "c",
             "nonce": "n1", "audience": "protean/vastvm", "exp": now + 10}
    report = {"lease_id": "L1", "genome_hash": "g", "cmd_sha": "c",
              "out_sha": "o", "status": "confirmed"}
    bundle = lease_proof.make_bundle(lease, report, {"out_sha": "o"}, key)
    verifier = lease_proof.Verifier(key)
    assert verifier.verify(bundle, now)["ok"] is True
    second = verifier.verify(lease_proof.make_bundle(lease, report,
                                                    {"out_sha": "o"}, key), now)
    assert second["ok"] is False
    assert "replay" in second["reasons"]
