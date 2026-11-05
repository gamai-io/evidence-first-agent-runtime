#!/usr/bin/env python3
"""Adversarial suite for proofgate (deterministic, script-style: exits 1 on failure)."""
import sys, os, json, hashlib, concurrent.futures
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from proofgate import check, verify, sha256_text
C = []
def ok(name, cond):
    C.append((name, bool(cond)))
def st(claims):
    return check(claims)["status"]
h = hashlib.sha256(b"proof").hexdigest()

ok("empty->unverified", st([]) == "unverified")
ok("num_int", st([{"text":"v","predicate":"eq_num","observed":1170,"expected":1170}]) == "confirmed")
ok("num_decimal_string", st([{"text":"v","predicate":"eq_num","observed":"1170.00","expected":1170}]) == "confirmed")
ok("num_tol_inside", st([{"text":"v","predicate":"eq_num","observed":1.0000000001,"expected":1}]) == "confirmed")
ok("num_tol_outside", st([{"text":"v","predicate":"eq_num","observed":1.00000001,"expected":1}]) == "refuted")
ok("num_negative", st([{"text":"v","predicate":"eq_num","observed":-5,"expected":-5}]) == "confirmed")
ok("num_zero", st([{"text":"v","predicate":"eq_num","observed":0,"expected":0}]) == "confirmed")
ok("num_huge", st([{"text":"v","predicate":"eq_num","observed":10**30,"expected":10**30}]) == "confirmed")
ok("num_nan_guard", st([{"text":"v","predicate":"eq_num","observed":"nan","expected":1}]) in ("unverified","refuted"))
ok("num_inf_guard", st([{"text":"v","predicate":"eq_num","observed":"inf","expected":1}]) in ("unverified","refuted"))
ok("num_bool_not_num", st([{"text":"v","predicate":"eq_num","observed":True,"expected":1}]) in ("confirmed","refuted","unverified"))
ok("str_accent", st([{"text":"s","predicate":"eq_str","observed":"Čevapi","expected":"cevapi"}]) == "confirmed")
ok("str_case", st([{"text":"s","predicate":"eq_str","observed":"SARAJEVO","expected":"sarajevo"}]) == "confirmed")
ok("str_space", st([{"text":"s","predicate":"eq_str","observed":"  a   b ","expected":"a b"}]) == "confirmed")
ok("str_diff", st([{"text":"s","predicate":"eq_str","observed":"mostar","expected":"sarajevo"}]) == "refuted")
ok("str_empty", st([{"text":"s","predicate":"eq_str","observed":"","expected":"x"}]) in ("unverified","refuted"))
ok("hash_ok", st([{"text":"h","predicate":"hash_eq","observed":h,"expected":h}]) == "confirmed")
ok("hash_case", st([{"text":"h","predicate":"hash_eq","observed":h.upper(),"expected":h}]) == "confirmed")
ok("hash_bad", st([{"text":"h","predicate":"hash_eq","observed":h,"expected":hashlib.sha256(b"x").hexdigest()}]) == "refuted")
ok("hash_nonhex", st([{"text":"h","predicate":"hash_eq","observed":"abc","expected":"abc"}]) == "confirmed")
ok("hash_missing", st([{"text":"h","predicate":"hash_eq","observed":None,"expected":h}]) == "unverified")
ok("rc0", st([{"text":"r","predicate":"rc_zero","observed":0}]) == "confirmed")
ok("rc1", st([{"text":"r","predicate":"rc_zero","observed":1}]) == "refuted")
ok("contains_ok", st([{"text":"c","predicate":"contains","observed":"x gama y","expected":"gama"}]) == "confirmed")
ok("contains_bad", st([{"text":"c","predicate":"contains","observed":"x","expected":"gama"}]) == "refuted")
ok("contains_empty_expected", st([{"text":"c","predicate":"contains","observed":"x","expected":""}]) == "unverified")
ok("json_subset", st([{"text":"j","predicate":"json_field_eq","observed":{"a":{"b":1,"c":2}},"expected":{"a":{"b":1}}}]) == "confirmed")
ok("json_missing", st([{"text":"j","predicate":"json_field_eq","observed":{"a":{"b":2}},"expected":{"a":{"b":1}}}]) == "refuted")
ok("json_list", st([{"text":"j","predicate":"json_field_eq","observed":{"l":[1,2]},"expected":{"l":[1,2]}}]) == "confirmed")
ok("json_list_diff", st([{"text":"j","predicate":"json_field_eq","observed":{"l":[1,3]},"expected":{"l":[1,2]}}]) == "refuted")
ok("unknown_pred", st([{"text":"u","predicate":"nope","observed":1,"expected":1}]) == "unverified")
ok("missing_expected", st([{"text":"m","predicate":"eq_num","observed":1}]) == "unverified")
ok("mixed_ref_dominates", st([{"text":"a","predicate":"rc_zero","observed":0},{"text":"b","predicate":"rc_zero","observed":2}]) == "refuted")
ok("mixed_unv_dominates", st([{"text":"a","predicate":"rc_zero","observed":0},{"text":"b","predicate":"eq_num","observed":None,"expected":1}]) == "unverified")
ok("dup_claims_counts", check([{"text":"a","predicate":"rc_zero","observed":0}]*2).get("counts",{}).get("confirmed") == 2)
r = check([{"text":"a","predicate":"rc_zero","observed":0}]); ok("verify_ok", verify(r).get("ok") is True)
r2 = json.loads(json.dumps(r)); r2["status"]="refuted"; ok("tamper_status", verify(r2).get("ok") is False)
r3 = json.loads(json.dumps(r)); r3["claims"][0]["observed"]=1; ok("tamper_observed", verify(r3).get("ok") is False)
h1=[check([{"text":"a","predicate":"rc_zero","observed":0}])["evidence_sha256"] for _ in range(50)]
ok("determinism", len(set(h1))==1)
def one(_):
    return check([{"text":"a","predicate":"eq_num","observed":7,"expected":7}])["status"]
with concurrent.futures.ThreadPoolExecutor(max_workers=16) as ex:
    outs=list(ex.map(one, range(1000)))
ok("concurrency", outs.count("confirmed")==1000)
ok("non_dict_claim", st([42]) == "unverified")
big=[{"text":"n%d"%i,"predicate":"eq_num","observed":i,"expected":i} for i in range(1000)]
ok("big_batch", check(big)["status"]=="confirmed")
bad=[n for n,v in C if not v]
print(json.dumps({"checks":len(C),"passed":len(C)-len(bad),"failed":len(bad),"failures":bad[:20]},indent=2))
sys.exit(0 if not bad else 1)
