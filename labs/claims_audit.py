#!/usr/bin/env python3
"""T7: bibliometric screen of common occult/wellness claims.

This is NOT a systematic review. It records how many OpenAlex works match a
claim's query and shows the top cited hits; the verdict is an editorial
classification, kept separate from the counts.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLAIMS = [
    ("528 Hz repairs DNA", "528 Hz DNA repair", "no controlled evidence"),
    ("Solfeggio frequencies heal", "solfeggio frequencies health", "no controlled evidence"),
    ("DNA has a specific electromagnetic frequency", "DNA electromagnetic frequency", "mechanism real; frequency code unproven"),
    ("Water memory (Benveniste)", "water memory Benveniste", "not replicated"),
    ("Chakras are measurable organs", "chakra measurement physiology", "no anatomical evidence"),
    ("Meditation changes brain structure", "meditation brain structure randomized", "supported by trials"),
    ("40 Hz gamma helps Alzheimer's", "40 Hz gamma Alzheimer randomized", "early/limited trials"),
    ("I Ching 64 maps to 64 codons", "I Ching genetic code", "arithmetic coincidence"),
    ("Pyramids focus energy", "pyramid energy experiment", "no credible evidence"),
    ("Piezo1 mediates mechanotransduction", "Piezo1 mechanotransduction", "strong evidence"),
]


def query(q: str) -> dict:
    url = ("https://api.openalex.org/works?search=" + urllib.parse.quote(q) +
           "&per-page=3&sort=cited_by_count:desc&mailto=labs@gamai.io")
    req = urllib.request.Request(url, headers={"User-Agent": "gamai-labs/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read().decode())
    return {
        "count": d.get("meta", {}).get("count", 0),
        "top": [
            {"title": w.get("title"), "year": w.get("publication_year"),
             "cites": w.get("cited_by_count"), "doi": w.get("doi")}
            for w in d.get("results", [])[:3]
        ],
    }


def main() -> int:
    rows = []
    for claim, q, verdict in CLAIMS:
        try:
            r = query(q)
            rows.append({"claim": claim, "query": q, "verdict": verdict, **r})
            print("%-50s hits=%-6d %s" % (claim, r["count"], verdict), flush=True)
        except Exception as exc:
            rows.append({"claim": claim, "query": q, "verdict": verdict, "error": str(exc)})
            print(claim, "ERROR", exc, flush=True)
    out = {"test": "OpenAlex bibliometric screen (not a systematic review)", "rows": rows}
    (HERE / "claims_audit_results.json").write_text(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
