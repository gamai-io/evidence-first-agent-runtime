#!/usr/bin/env python3
"""Adversarial suite for gamai_guard: lease scoping, approvals, pinned exec."""
import sys, os, hashlib
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
from gamai_guard.plan import Lease, check
from gamai_guard.cbr import Proposal, ApprovalStore, evaluate
from gamai_guard.executed import run_pinned
C=[]
def ok(n,c): C.append((n,bool(c)))
def d(steps, effects): return check({"id":"t","steps":steps}, Lease.from_dict({"effects":effects}))
ok("scoped_allow", d([{"op":"fs.read","path":"/in/a"}], {"fs.read":["/in"]})["allow"])
ok("escape_deny", not d([{"op":"fs.read","path":"/etc/passwd"}], {"fs.read":["/in"]})["allow"])
ok("prefix_confusion", not d([{"op":"fs.read","path":"/input/a"}], {"fs.read":["/in"]})["allow"])
ok("traversal", not d([{"op":"fs.read","path":"/in/../etc/passwd"}], {"fs.read":["/in"]})["allow"])
ok("unknown_op", not d([{"op":"net.fetch","url":"http://x"}], {"fs.read":["/in"]})["allow"])
ok("no_effects", not d([{"op":"fs.read","path":"/in/a"}], {})["allow"])
ok("multi_one_bad", not d([{"op":"fs.read","path":"/in/a"},{"op":"fs.read","path":"/etc/x"}], {"fs.read":["/in"]})["allow"])
ok("multi_all_ok", d([{"op":"fs.read","path":"/in/a"},{"op":"fs.read","path":"/in/b"}], {"fs.read":["/in"]})["allow"])
ok("empty_steps_bool", isinstance(d([], {"fs.read":["/in"]}).get("allow"), bool))
p=Proposal(intent="i",goal="g",evidence=["e"],proposer="alice",approver="bob",ok=5,fail=0)
ok("ready_when_good", evaluate(p)["ready"] is True)
ok("not_ready_few_ev", evaluate(Proposal(intent="i",goal="g",evidence=["e"],proposer="a",approver="b",ok=4,fail=0))["ready"] is False)
ok("not_ready_fail", evaluate(Proposal(intent="i",goal="g",evidence=["e"],proposer="a",approver="b",ok=5,fail=1))["ready"] is False)
ok("not_ready_noev", evaluate(Proposal(intent="i",goal="g",evidence=[],proposer="a",approver="b",ok=5,fail=0))["ready"] is False)
ok("not_ready_same", evaluate(Proposal(intent="i",goal="g",evidence=["e"],proposer="a",approver="a",ok=5,fail=0))["ready"] is False)
ok("risky_goal", "risky_goal" in evaluate(Proposal(intent="rm -rf",goal="delete",evidence=["e"],proposer="a",approver="b",ok=9,fail=0))["risk"])
import tempfile
key=b"k"*32; db=tempfile.mktemp()
s=ApprovalStore(db,key)
ok("approve_ok", s.approve(p)["ok"] is True)
ok("check_ok", s.check(p) is True)
ok("different_key", ApprovalStore(db,b"z"*32).check(p) is False)
ok("tampered_proposal", s.check(Proposal(intent="i",goal="g",evidence=["e2"],proposer="alice",approver="bob",ok=5,fail=0)) is False)
ok("unknown_intent", s.check(Proposal(intent="x",goal="g",evidence=["e"],proposer="a",approver="b",ok=5,fail=0)) is False)
ok("same_principal_denied", s.approve(Proposal(intent="j",goal="g",evidence=["e"],proposer="a",approver="a",ok=9,fail=0))["ok"] is False)
true_sha=hashlib.sha256(open("/bin/true","rb").read()).hexdigest()
r=run_pinned("/bin/true", true_sha)
r2=run_pinned("/bin/true", "0"*64)
ok("pinned_wrong_hash", r2.get("ok") is False)
bad=[n for n,v in C if not v]
print({"checks":len(C),"passed":len(C)-len(bad),"failed":len(bad),"failures":bad[:20]})
sys.exit(0 if not bad else 1)
