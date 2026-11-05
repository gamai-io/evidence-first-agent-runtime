#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pravi reproducibilni bench paket: kod + zadaci + sirovi JSONL + log + sha256."""
import argparse, hashlib, json, os, platform, shutil, subprocess, sys, time
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--run-jsonl",required=True)
    ap.add_argument("--prompts",default="prompts_v2.json")
    ap.add_argument("--log",default="")
    ap.add_argument("--out",required=True)
    ap.add_argument("--model",default="")
    ap.add_argument("--mode",default="model")
    a=ap.parse_args()
    D=a.out; os.makedirs(D,exist_ok=True)
    for d in ("code","data","results","logs"): os.makedirs(os.path.join(D,d),exist_ok=True)
    for f in ("run_bench.py","grade.py","check_results.py","serve_and_bench.sbatch","README.md",a.prompts,"results.schema.json"):
        if os.path.exists(f): shutil.copy2(f,os.path.join(D,"code" if f.endswith((".py",".sbatch",".md")) else "data"))
    shutil.copy2(a.run_jsonl,os.path.join(D,"results","raw.jsonl"))
    if a.log and os.path.exists(a.log): shutil.copy2(a.log,os.path.join(D,"logs",os.path.basename(a.log)))
    files=[]
    for root,_,fs in os.walk(D):
        for fn in fs:
            p=os.path.join(root,fn); files.append((os.path.relpath(p,D),sha(p),os.path.getsize(p)))
    man={"created":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
         "host":platform.node(),"python":platform.python_version(),"platform":platform.platform(),
         "model":a.model,"mode":a.mode,"prompts":os.path.basename(a.prompts),
         "prompts_sha256":sha(os.path.join(D,"data",os.path.basename(a.prompts))) if os.path.exists(os.path.join(D,"data",os.path.basename(a.prompts))) else None,
         "git":"", "files":{f:{"sha256":s,"bytes":b} for f,s,b in files}}
    try: man["git"]=subprocess.check_output(["git","rev-parse","HEAD"],stderr=subprocess.DEVNULL).decode().strip()
    except Exception: pass
    json.dump(man,open(os.path.join(D,"MANIFEST.json"),"w"),indent=2)
    with open(os.path.join(D,"SHA256SUMS"),"w") as f:
        for rel,s,b in sorted(files): f.write(f"{s}  {rel}\n")
    repro=f"""# Reprodukcija

1. Okruzenje: {platform.platform()} / Python {platform.python_version()} / host {platform.node()}
2. Zadaci: `{os.path.basename(a.prompts)}` (sha256 {man['prompts_sha256']})
3. Pokretanje (model-mode, temperature=0, seed=42):
   `python3 run_bench.py --mode model --url <vllm> --set model_plane --n <N> --out results/raw.jsonl --run-id <id>`
4. Semanticko ocjenjivanje:
   `python3 grade.py --jsonl results/raw.jsonl --prompts {os.path.basename(a.prompts)} --md report.md --json-out grade.json`
5. Integritet: `sha256sum -c SHA256SUMS`

Napomena: guard/fastpath rezultati se NE racunaju kao model. Ako je koristen harness `/chat`, u JSONL mora biti `mode=harness` i rezultat se prijavljuje odvojeno.
"""
    open(os.path.join(D,"REPRO.md"),"w").write(repro)
    print("pack:",D,"files:",len(files))
if __name__=="__main__": main()
