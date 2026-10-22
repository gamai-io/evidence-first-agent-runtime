#!/usr/bin/env python3
"""T4: 40 Hz gamma entrainment literature gate.

This is a scoping audit, not a meta-analysis. It asks whether there are enough
human randomized/sham-controlled studies with extractable outcomes to justify
one. OpenAlex metadata only; full-text effect sizes are not extracted here.
"""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request

QUERIES = [
    '"40 Hz" gamma entrainment Alzheimer',
    '"40 Hz" gamma sensory stimulation randomized',
    'gamma entrainment cognition randomized',
]
BASE = "https://api.openalex.org/works"
MAIL = "admin@gamai.io"


def fetch(query: str, per_page: int = 50) -> list[dict]:
    params = urllib.parse.urlencode({
        "search": query,
        "per-page": per_page,
        "filter": "from_publication_date:2015-01-01",
        "mailto": MAIL,
    })
    req = urllib.request.Request(BASE + "?" + params,
                                 headers={"User-Agent": "gamai-labs/0.1"})
    data = json.load(urllib.request.urlopen(req, timeout=30))
    return data.get("results", [])


def abstract(work: dict) -> str:
    inv = work.get("abstract_inverted_index") or {}
    words = []
    for word, positions in inv.items():
        for p in positions:
            words.append((p, word))
    return " ".join(w for _, w in sorted(words))


def main() -> int:
    seen = {}
    for q in QUERIES:
        try:
            rows = fetch(q)
        except Exception as exc:
            print("query failed:", q, exc)
            continue
        for w in rows:
            key = w.get("doi") or w.get("id")
            if key in seen:
                continue
            text = " ".join([w.get("display_name") or "", abstract(w)])
            low = text.lower()
            seen[key] = {
                "title": (w.get("display_name") or "")[:160],
                "year": w.get("publication_year"),
                "doi": w.get("doi"),
                "type": w.get("type"),
                "human": bool(re.search(r"\b(patients?|participants?|subjects?|adults?|human)\b", low)),
                "animal": bool(re.search(r"\b(mice|mouse|rats?|5xfad|app/ps1)\b", low)),
                "randomized": bool(re.search(r"\b(randomi[sz]ed|placebo|sham[- ]controlled)\b", low)),
                "gamma": bool(re.search(r"40\s*hz|gamma", low)),
                "review_or_protocol": bool(re.search(
                    r"\b(review|meta-analysis|scoping review|study protocol|protocol for)\b", low)),
                "alzheimer": bool(re.search(r"alzheimer|mild cognitive impairment|\bmci\b", low)),
                "cognition": bool(re.search(r"cognit|memory|attention|executive", low)),
                "other_neuromod": bool(re.search(
                    r"\b(tacs|tdcs|trns|transcranial|vibroacoustic|fibromyalgia|pain)\b", low)),
            }
    rows = list(seen.values())
    human = [r for r in rows if r["human"] and not r["animal"]]
    rcts = [r for r in human if r["randomized"]]
    relevant = [r for r in rcts if not r["review_or_protocol"]
                and not r["other_neuromod"]
                and (r["alzheimer"] or r["cognition"])]
    animal = [r for r in rows if r["animal"]]
    res = {
        "test": "40 Hz gamma literature gate",
        "unique_works": len(rows),
        "human_works": len(human),
        "human_randomized_or_sham": len(rcts),
        "relevant_rct_like": len(relevant),
        "animal_works": len(animal),
        "verdict": (
            "meta-analysis is NOT justified yet: fewer than 10 relevant human RCT-like records"
            if len(relevant) < 10 else
            "at least 10 relevant human RCT-like records; extract full-text effects"
        ),
        "rct_sample": [{"title": r["title"], "year": r["year"], "doi": r["doi"],
                        "review_or_protocol": r["review_or_protocol"],
                        "alzheimer": r["alzheimer"], "cognition": r["cognition"],
                        "other_neuromod": r["other_neuromod"]}
                       for r in rcts[:12]],
        "limits": "OpenAlex metadata/abstracts only; no effect sizes, no GRADE, no full-text review",
    }
    (Path := __import__("pathlib").Path)(__file__).with_name("gamma_audit_results.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
