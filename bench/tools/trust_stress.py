import sys,json,random,hashlib,time
sys.path.insert(0,"/scratch/project_465003647/efar/proofgate")
from proofgate import check,verify
rnd=random.Random(42); C=[]
def A(kind,claims,exp): C.append((kind,claims,exp))
h=hashlib.sha256(b"proof").hexdigest()
for i in range(1200):
    n=rnd.randint(0,10**6); A("eq_num_ok",[{"text":"n","predicate":"eq_num","observed":n,"expected":n}],"confirmed")
    A("eq_num_bad",[{"text":"n","predicate":"eq_num","observed":n,"expected":n+1}],"refuted")
    A("hash_ok",[{"text":"h","predicate":"hash_eq","observed":h,"expected":h}],"confirmed")
    A("hash_bad",[{"text":"h","predicate":"hash_eq","observed":h,"expected":hashlib.sha256(str(i).encode()).hexdigest()}],"refuted")
    A("rc0",[{"text":"rc","predicate":"rc_zero","observed":0}],"confirmed")
    A("rc1",[{"text":"rc","predicate":"rc_zero","observed":1}],"refuted")
    A("contains_ok",[{"text":"c","predicate":"contains","observed":"gama-ok-%d"%i,"expected":"gama-ok"}],"confirmed")
    A("contains_bad",[{"text":"c","predicate":"contains","observed":"xx","expected":"gama-ok"}],"refuted")
    A("str_ok",[{"text":"s","predicate":"eq_str","observed":" Sarajevo ","expected":"sarajevo"}],"confirmed")
    A("str_bad",[{"text":"s","predicate":"eq_str","observed":"Mostar","expected":"sarajevo"}],"refuted")
    A("missing",[{"text":"m","predicate":"eq_num","observed":None,"expected":1}],"unverified")
    A("unknown_pred",[{"text":"u","predicate":"nope","observed":1,"expected":1}],"unverified")
    A("mixed_ref",[{"text":"a","predicate":"rc_zero","observed":0},{"text":"b","predicate":"rc_zero","observed":2}],"refuted")
    A("mixed_unv",[{"text":"a","predicate":"rc_zero","observed":0},{"text":"b","predicate":"eq_num","observed":None,"expected":1}],"unverified")
    A("json_ok",[{"text":"j","predicate":"json_field_eq","observed":{"a":{"b":1}},"expected":{"a":{"b":1}}}],"confirmed")
    A("json_bad",[{"text":"j","predicate":"json_field_eq","observed":{"a":{"b":2}},"expected":{"a":{"b":1}}}],"refuted")
    A("dec_ok",[{"text":"d","predicate":"eq_num","observed":"1170.00","expected":1170}],"confirmed")
    A("unicode",[{"text":"u","predicate":"eq_str","observed":"Čevapi","expected":"cevapi"}],"confirmed")
rnd.shuffle(C); C=C[:10000]
fa=fr=un=ok=0; lat=[]; tamper_ok=0; tamper_n=0; det=0
for kind,claims,exp in C:
    t=time.perf_counter(); r=check(claims); lat.append((time.perf_counter()-t)*1000)
    st=r.get("status")
    if st!=exp:
        if st=="confirmed" and exp!="confirmed": fa+=1
        elif st=="refuted" and exp=="confirmed": fr+=1
        elif st=="unverified" and exp!="unverified": un+=1
    else: ok+=1
    if exp in ("refuted","unverified"):
        tamper_n+=1
        r2=json.loads(json.dumps(r)); r2["status"]="confirmed"
        try:
            if not verify(r2).get("ok",True): tamper_ok+=1
        except Exception: tamper_ok+=1
    if i<50:
        r3=check(claims)
        if r3.get("evidence_sha256")==r.get("evidence_sha256"): det+=1
res={"n":len(C),"match":ok,"mismatch":len(C)-ok,"false_accept":fa,"false_refute":fr,"wrong_unverified":un,
"tamper_detect":tamper_ok,"tamper_n":tamper_n,"determinism_50":det,"avg_ms":round(sum(lat)/len(lat),4),
"p99_ms":round(sorted(lat)[int(0.99*len(lat))],4)}
print(json.dumps(res,indent=2))
open("/scratch/project_465003647/trust_stress_result.json","w").write(json.dumps(res,indent=2))
