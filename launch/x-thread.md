# X/Twitter thread draft (9 tweets)

1/
Your agent says "done".
The file does not exist.
The machine timed out.
The action ran in the wrong session.

We built three small components that make those lies measurable — and
preventable. Open source, MIT, one command to reproduce. 🧵

2/
**proofgate**: every claim is `confirmed`, `refuted`, or `unverified`.

Missing evidence is never `confirmed`. Change one number and the report is
`tampered`.

Demo: 10 confirmed, 2 refuted, 0 unverified.

3/
Why `refuted` matters:

A gate that only says "ok" is a confidence score.
A gate that can say "no, and here is the hash" is an audit trail.

4/
**agent-immunity**: blocked injections become antibodies.

Baseline: 10/10 attacks succeed.
Filter only: one reworded payload escapes (10% in round 2).
With memory: 0% / 0% / 0%, utility 100%, false denial 0%, ~1.3 ms.

5/
It normalizes NFKC, strips zero-width/bidi, folds homoglyphs, decodes base64,
then matches exact + near-miss.

A block is not a dead end. It is training data.

6/
**crossnode-bench**: scores the claim, not the answer.

Two nodes claim `ok:true` for a missing program and a missing app.
Naive scorer: 48/48.
CrossNode: 46/48 + names both lies.

7/
On a real Windows/Linux/Android fleet we reproduced three false-success
classes: missing program, missing Android package, GUI action in Session 0.

This is the gap between a demo and production.

8/
Everything is stdlib Python. No keys. No network.

```
git clone …
./repro.sh
```

16/16, 28/28, 10/10 tests. Numbers, limitations, and raw eval output in the
repo.

9/
We are not claiming SOTA. We are claiming these three properties should be
measurable in every agent runtime:

proof · immunity · honesty

Run it, break it, tell us where it fails. Links in the next tweet. 👇
