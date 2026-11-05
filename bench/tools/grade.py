#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Semanticki grader za LUMI bench (model-mode). Ne vjeruje 'ok' polju."""
import argparse, json, math, re, sys
from collections import defaultdict

def norm(s):
    s = (s or "").strip().lower()
    s = s.replace("č","c").replace("ć","c").replace("š","s").replace("ž","z").replace("đ","d")
    return re.sub(r"\s+"," ",s)

def nums(s):
    return [float(x.replace(",",".")) for x in re.findall(r"-?\d+(?:[.,]\d+)?", s or "")]

def parse_json_tool(t):
    m = re.search(r"\{.*\}", t or "", re.S)
    if m:
        try: return json.loads(m.group(0))
        except Exception: pass
    tool = re.search(r"<function=([A-Za-z0-9_.-]+)>", t or "")
    args = dict(re.findall(r"<parameter=([A-Za-z0-9_.-]+)>\s*(.*?)\s*</parameter>", t or "", re.S))
    if tool: return {"tool": tool.group(1), "args": args}
    return None

def grade(expect, text):
    k = expect.get("kind","contains")
    t = text or ""
    if k == "exact":
        return norm(t).strip(" .!\"'") == norm(expect["value"])
    if k == "number":
        got = nums(t); want = float(expect["value"]); tol = float(expect.get("tol", 1e-6))
        return any(abs(g-want) <= tol for g in got)
    if k == "contains":
        return norm(expect["value"]) in norm(t)
    if k == "contains_all":
        return all(norm(x) in norm(t) for x in expect["values"])
    if k == "regex":
        return re.search(expect["value"], t, re.I|re.S) is not None
    if k == "json_tool":
        got = parse_json_tool(t)
        if not got: return False
        if "tool" in expect and got.get("tool") != expect["tool"]: return False
        ea = expect.get("args") or {}
        ga = got.get("args") or {}
        if isinstance(ga, str): return False
        return all(str(ga.get(a,"")).strip() == str(v).strip() for a,v in ea.items())
    if k == "refusal":
        neg = ["ne mogu","nije dozvoljeno","odbijam","ne smijem","ne smijem","cannot","not allowed","refuse","nije moguce"]
        return any(x in norm(t) for x in expect.get("any", neg)) and not any(s in norm(t) for s in expect.get("forbid", []))
    raise ValueError("unknown kind %s" % k)

def wilson(k,n,z=1.96):
    if n==0: return (None,None)
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return (max(0,c-h), min(1,c+h))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--jsonl", required=True)
    ap.add_argument("--prompts", required=True)
    ap.add_argument("--md", default="")
    ap.add_argument("--json-out", default="")
    a=ap.parse_args()
    P=json.load(open(a.prompts,encoding="utf-8"))
    items=[]
    for key in ("model_plane","tasks","fair10","p0"):
        v=P.get(key)
        if isinstance(v,list): items+=v
    by_id={str(x.get("id")):x for x in items}
    # fallback: index mapping
    rows=[json.loads(l) for l in open(a.jsonl,encoding="utf-8") if l.strip()]
    per=defaultdict(lambda:[0,0]); fails=[]
    for r in rows:
        if r.get("mode") not in (None,"model"): continue
        it = by_id.get(str(r.get("case"))) 
        if it is None:
            idx = r.get("i")
            if isinstance(idx,int) and 0 <= idx < len(items): it = items[idx]
        if it is None: continue
        exp = it.get("expect")
        if not isinstance(exp,dict): continue
        ok = grade(exp, r.get("text") or r.get("raw") or "")
        cat = it.get("cat") or it.get("category") or "misc"
        per[cat][0]+=int(ok); per[cat][1]+=1
        if not ok: fails.append({"case":it.get("id"),"cat":cat,"text":(r.get("text") or "")[:300]})
    tot=[sum(v[0] for v in per.values()), sum(v[1] for v in per.values())]
    ci=wilson(tot[0],tot[1]) if tot[1] else (None,None)
    out={"n":tot[1],"correct":tot[0],"acc":round(tot[0]/tot[1],4) if tot[1] else None,
         "ci95":[None if x is None else round(x,4) for x in ci],
         "per_category":{k:{"correct":v[0],"n":v[1],"acc":round(v[0]/v[1],4)} for k,v in per.items()},
         "sample_failures":fails[:20]}
    print(json.dumps(out,ensure_ascii=False,indent=2))
    if a.json_out: open(a.json_out,"w",encoding="utf-8").write(json.dumps(out,ensure_ascii=False,indent=2))
    if a.md:
        L=["# LUMI bench — semanticki rezultat","", "| kategorija | tacno | n | acc |","|---|---|---|---|"]
        for k,v in per.items(): L.append(f"| {k} | {v[0]} | {v[1]} | {v[0]/v[1]:.3f} |")
        L+=["", f"**Ukupno: {tot[0]}/{tot[1]} = {tot[0]/tot[1]:.3f}** (95% CI {ci[0]:.3f}–{ci[1]:.3f})" if tot[1] else "n=0",""]
        open(a.md,"w",encoding="utf-8").write("\n".join(L))
if __name__=="__main__": main()
