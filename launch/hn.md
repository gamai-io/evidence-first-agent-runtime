# Show HN draft

**Title (70 chars):**
`Show HN: An agent runtime that refuses to claim what it can't prove`

**URL:** https://github.com/gamai-labs/evidence-first-agent-runtime

**Text:**

Most agent demos optimize what the model can do. We optimized what you can
trust, and measured the difference.

Three small, dependency-free components:

1. **proofgate** — an agent's claim is checked against external evidence and
   returns `confirmed`, `refuted`, or `unverified`, bound to a SHA-256.
   Missing evidence is never `confirmed`. Tampering breaks verification. On
   the built-in suite: 10 confirmed, 2 refuted, 0 unverified.

2. **agent-immunity** — provenance taint plus antibody memory. Every blocked
   injection becomes a signature (exact + near-miss after NFKC, zero-width and
   homoglyph folding). On a 10-payload × 3-channel × 3-round corpus: baseline
   injection success 100%, filter-only 0/10/0% (a reworded payload escapes),
   with memory 0/0/0%, utility 100%, false denial 0%, ~1.3 ms per check.

3. **crossnode-bench** — scores the claim, not the answer. A node that says
   `ok:true` after a timeout is recorded as a *false success*. The demo
   detects 2 lies that a naive scorer counts as passes (46/48, not 48/48). A
   reference run on a real Windows/Linux/Android fleet reproduced three
   classes of false success.

`./repro.sh` runs everything offline with the Python standard library. No
keys, no database, no network.

What we'd like from HN: run it, try to break the near-miss matcher, and tell
us where the false-positive rate becomes unacceptable for your traffic.

Limitations are in the README: synthetic injection corpus, lexical near-miss,
small-N harness benchmarks. We are not claiming SOTA — we are claiming that
these three properties should be measurable in every agent runtime.

Happy to answer questions about the failure modes, the isolation ladder
(bwrap → runc → seccomp → gVisor), or how to integrate the gate into an
existing tool loop.
