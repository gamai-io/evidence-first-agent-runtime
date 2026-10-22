# Product Hunt draft

**Name:** Evidence-first agent runtime

**Tagline (60 chars):**
`Agents that prove what they did — or say they couldn't.`

**Topics:** Developer Tools, Artificial Intelligence, Open Source, Security

**Description:**

AI agents are confident even when they are wrong. This runtime makes three
properties measurable:

- **Proof.** Every claim is `confirmed`, `refuted`, or `unverified`, with a
  tamper-evident hash. Missing evidence never becomes "done".
- **Immunity.** Blocked prompt injections become antibodies, so a reworded or
  homoglyph-obfuscated variant is stopped on the next turn. Injection success
  100% → 0% in three rounds, ~1.3 ms overhead.
- **Honesty.** A cross-node benchmark scores the agent's claim against ground
  truth and reports false success — the failures that make demos look perfect
  and production break.

Open source, MIT, Python standard library only. One command reproduces every
number: `./repro.sh`.

**First comment:**

We built this after watching agents report "done" for files that did not
exist, and "ok" for machines that timed out. The fix is not a better prompt;
it is a gate, a memory, and a benchmark. All three are small enough to read
in an afternoon. Try to break them and tell us what you find — especially the
false-positive rate of the near-miss matcher on your own text.
