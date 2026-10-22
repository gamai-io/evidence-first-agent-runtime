# Reddit drafts

## r/LocalLLaMA

**Title:** We made an agent gate that returns "refuted" instead of hallucinating, and a benchmark that measures false success across machines

**Body:**

Most agent stacks report `ok:true` and let the human discover the truth. We
built three small pieces to change that, all MIT and stdlib-only:

1. **proofgate** — claims are checked against external evidence:
   `confirmed` / `refuted` / `unverified`, bound to SHA-256. Missing evidence
   is never confirmed. Demo: 10 confirmed, 2 refuted, 0 unverified.
2. **agent-immunity** — taint + antibody memory. Injection success 100% →
   0% in three rounds, utility 100%, false denial 0%, ~1.3 ms/check. Filter
   only leaks a reworded payload (10% in round 2); memory closes it.
3. **crossnode-bench** — compares each node's claim with ground truth. Demo
   catches 2 false successes (46/48). Real fleet: missing program, missing
   Android package, GUI action in Session 0.

`./repro.sh` reproduces everything offline. No keys.

We would especially value criticism of the near-miss matcher (Jaccard/overlap
≥ 0.80 after normalization): where does it false-positive on your text?
Limitations are documented; this is not a SOTA claim.

## r/AI_Agents

**Title:** Three properties every agent runtime should measure: proof, immunity, honesty — with reproducible numbers

**Body:**

Short version: we open-sourced the measurement, not just the demo.

- proof — can the agent say "refuted" when evidence is absent?
- immunity — does a blocked injection make the next variant cheaper to block?
- honesty — does the agent claim success on machines where nothing happened?

Repo contains 3 components, 54 tests total (16 + 28 + 10), and a single
`repro.sh`. Numbers and limitations in the README. Feedback welcome,
especially from people running agents across heterogeneous machines.

## r/netsec (immunity focus)

**Title:** Learned antibodies for prompt injection: 100% → 0% ASR in 3 rounds, with utility and false-denial measured

**Body:**

We treat a blocked prompt injection as a signature, not just a dropped
request. The defense normalizes NFKC/zero-width/bidi/homoglyphs, decodes
base64, then matches exact and near-miss (Jaccard/overlap ≥ 0.80), with
0.98/day decay.

Synthetic corpus: 10 payloads × 3 channels (memory/tool/skill) × 3 rounds.
Baseline ASR 100%. Filter-only: 0/10/0% — a reworded payload escapes. With
antibody memory: 0/0/0%, utility 100%, false denial 0%, ~1.3 ms/check.

This is not a replacement for model-level defenses, and the corpus is
synthetic. We are publishing the harness so the false-positive rate can be
argued with data. Code + raw eval JSON in the repo; happy to discuss where
lexical near-miss breaks.
