# 90-second demo video — shot list

Format: 1920×1080, screen recording + large captions, no private UI, no
machine names, no keys. Voice: calm, English. Music: none or very low.

| Time | Visual | Voice / caption |
|---|---|---|
| 0:00–0:08 | Terminal: baseline agent says "Done — file created at /tmp/report.md". `ls` shows nothing. | "An agent said it created a file. It didn't." |
| 0:08–0:20 | Same task through `proofgate`. Output: `status: refuted`, `counts: confirmed 0, refuted 1`, hash. | "A claim should be able to fail. Missing evidence is never 'confirmed'." |
| 0:20–0:28 | Show `verify report.json` → ok; edit one number → `tampered: true`. | "And the record is tamper-evident." |
| 0:28–0:40 | Table: baseline 100% / filter 0-10-0 / memory 0-0-0. Highlight round 2. | "Filters stop the payload. They don't stop the paraphrase." |
| 0:40–0:55 | Terminal: round 1 injection blocked, antibody added; round 2 reworded payload blocked by near-miss; stats show hits. | "A block becomes an antibody. The defense learns." |
| 0:55–1:00 | Overlay: utility 100%, false denial 0%, 1.3 ms. | "Without sacrificing useful work." |
| 1:00–1:12 | CrossNode demo: 46/48, two red rows named "false success". | "Most benchmarks score the answer. This one scores the claim." |
| 1:12–1:20 | Three probe screenshots: missing program, missing app, Session 0. | "These are the lies that survive a demo and break production." |
| 1:20–1:30 | `./repro.sh` running, final "OK". Repo URL + MIT. | "Three components. One command. No keys. Run it, try to break it." |

## Caption pack (for X/LinkedIn)

- "Your agent says done. The file doesn't exist."
- "A claim should be able to fail: confirmed / refuted / unverified."
- "A block is training data: injection success 100% → 0% in 3 rounds."
- "Naive scorer: 48/48. CrossNode: 46/48 + names the two lies."
- "Open source, MIT, stdlib only. `./repro.sh`."
