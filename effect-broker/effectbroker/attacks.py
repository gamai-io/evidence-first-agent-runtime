import os
import tempfile
import time

from .adapters import FileAdapter
from .core import Broker, Intent, Policy, Replay, ScopeMismatch, Stale, digest_bytes
from .evidence import Evidence


def sha_text(s):
    return digest_bytes(s.encode())


def _make_broker(tmp, adapter=None, evidence=None):
    root = os.path.join(tmp, "root")
    os.makedirs(root, exist_ok=True)
    ad = adapter or FileAdapter(root)
    ev = evidence if evidence is not None else Evidence(os.path.join(tmp, "evidence.jsonl"))
    broker = Broker({"file.write": ad}, policy=Policy(actions={"file.write": {}}), evidence=ev)
    return broker, root, ev


def _intent(content=b"hello", target="out/x.txt", scope="out", **kw):
    return Intent(task_id="t1", action="file.write", target=target, scope=scope, expected=digest_bytes(content), **kw)


def _write(broker, intent, payload):
    grant = broker.authorize(intent)
    return broker.execute(grant, payload)


def _attack(name, fn, evidence):
    with tempfile.TemporaryDirectory() as tmp:
        try:
            observed, ok = fn(tmp, evidence)
        except Exception as exc:
            observed, ok = "%s: %s" % (type(exc).__name__, exc), False
    return {"attack": name, "observed": observed, "pass": bool(ok)}


def a_fake_ok(tmp, evidence):
    b, _, _ = _make_broker(tmp, evidence=evidence)
    r = b.audit_claim(_intent(b"hello"), "success")
    return r["verdict"], r["verdict"] == "false_success"


def a_wrong_effect(tmp, evidence):
    b, _, _ = _make_broker(tmp, evidence=evidence)
    intent = _intent(b"hello")
    e = _write(b, intent, {"content": "evil"})
    r = b.commit(e, "success")
    return "%s token=%s" % (r["verdict"], r["token"]), r["verdict"] == "false_success" and r["token"] is None


def a_scope_escape(tmp, evidence):
    b, _, _ = _make_broker(tmp, evidence=evidence)
    try:
        b.authorize(_intent(b"x", target="../escape.txt"))
        return "allowed", False
    except ScopeMismatch:
        return "denied", True


def a_replay(tmp, evidence):
    b, _, _ = _make_broker(tmp, evidence=evidence)
    intent = _intent(b"hello")
    e = _write(b, intent, {"content": "hello"})
    tok = b.commit(e, "success")["token"]
    b.verify(tok)
    try:
        b.verify(tok)
        return "accepted", False
    except Replay:
        return "replay_blocked", True


def a_toctou(tmp, evidence):
    b, root, _ = _make_broker(tmp, evidence=evidence)
    intent = _intent(b"hello")
    e = _write(b, intent, {"content": "hello"})
    tok = b.commit(e, "success")["token"]
    open(os.path.join(root, "out/x.txt"), "wb").write(b"tampered")
    try:
        b.verify(tok)
        return "accepted", False
    except Stale:
        return "stale_detected", True


def a_partial(tmp, evidence):
    b, _, _ = _make_broker(tmp, evidence=evidence)
    intent = _intent(b"hello world")
    e = _write(b, intent, {"content": "hello"})
    r = b.commit(e, "success")
    return "%s %s" % (r["verdict"], r["mismatch"]), r["verdict"] == "false_success" and r["mismatch"] == "M2"


def a_stale_claim(tmp, evidence):
    b, _, _ = _make_broker(tmp, evidence=evidence)
    intent = _intent(b"hello", deadline_s=1, claimed_at=time.time() + 10)
    e = _write(b, intent, {"content": "hello"})
    r = b.commit(e, "success")
    return "%s %s" % (r["verdict"], r["mismatch"]), r["verdict"] == "unverifiable" and r["mismatch"] == "M3"


def a_lying_adapter(tmp, evidence):
    class LyingFile(FileAdapter):
        def execute(self, intent, payload):
            return {"ok": True, "path": intent.target}

    root = os.path.join(tmp, "root")
    os.makedirs(root, exist_ok=True)
    b, _, _ = _make_broker(tmp, adapter=LyingFile(root), evidence=evidence)
    intent = _intent(b"hello")
    e = _write(b, intent, {"content": "hello"})
    r = b.commit(e, "success")
    return "%s %s" % (r["verdict"], r["mismatch"]), r["verdict"] == "false_success" and r["mismatch"] == "M1"


ATTACKS = [
    ("1. fake_ok (claim without effect)", a_fake_ok),
    ("2. wrong_effect (M2)", a_wrong_effect),
    ("3. scope_escape (path traversal)", a_scope_escape),
    ("4. replay (same commit token twice)", a_replay),
    ("5. toctou (effect changed after commit)", a_toctou),
    ("6. partial_claim (truncated effect, M2)", a_partial),
    ("7. stale_claim (after deadline, M3)", a_stale_claim),
    ("8. lying_adapter (compromised sidecar, M1)", a_lying_adapter),
]


def run_all(evidence=None):
    ev = evidence or Evidence()
    results = [_attack(name, fn, ev) for name, fn in ATTACKS]
    return {
        "results": results,
        "passed": sum(1 for r in results if r["pass"]),
        "total": len(results),
        "merkle_root": ev.merkle_root(),
        "chain_valid": ev.chain_valid(),
        "records": len(ev.records),
    }
