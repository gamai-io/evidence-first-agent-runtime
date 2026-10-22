# The agent that says "refuted"

*Draft — publish only after approval.*

An agent told me a file was created. It gave me a path, a size, and a cheerful
confirmation. The file did not exist. Nothing had run. The model had done what
models do: it completed the most plausible next sentence.

That was not a model bug. It was an architecture bug. We had given the agent a
tool loop and a text channel, but no way to distinguish *what it did* from
*what it said*. Most agent stacks still have this hole. They optimize
capability — more tools, longer context, faster inference — while trust is
left to a sentence in the system prompt: "do not hallucinate."

We spent the last week building the missing measurement layer. It is three
small open-source components, MIT, Python standard library only. One command
reproduces every number.

## 1. Proof: a claim should be able to fail

`proofgate` takes a claim as `observed` versus `expected` under a deterministic
predicate — numeric equality, string equality, hash equality, return code,
substring, JSON subset. It returns one of three statuses:

- `confirmed`: evidence is present and the predicate holds
- `refuted`: evidence is present and the predicate does **not** hold
- `unverified`: evidence is missing, malformed, or the predicate is unknown

The aggregation is fail-closed: one refuted claim makes the report refuted;
one unverified claim prevents "confirmed". No claims is unverified, not
vacuously true. The report is bound to a SHA-256; change a single value and
verification reports tampering.

The built-in demo contains ten true claims and two false ones. A gate that
returns "all good" would be broken; ours returns `confirmed=10, refuted=2,
unverified=0`.

Why does this matter? Because "are you sure?" is still a claim. A real gate
needs an observation that lives outside the model, a predicate that does not
negotiate, and a record that can be checked later.

## 2. Immunity: a block should become memory

Prompt injection is usually treated as a filtering problem: detect the bad
string, drop the request. That works until the attacker changes one word.

`agent-immunity` treats a blocked injection as a signature. It normalizes
NFKC, strips zero-width and bidi characters, folds common homoglyphs, decodes
base64, and then matches both exactly and by near-miss (Jaccard or overlap
coefficient ≥ 0.80, with a minimum token count). Every block is stored as an
"antibody" with a severity and a decay of 0.98 per day. It also tracks
provenance: content from an untrusted source is `untrusted`, external content
is `quarantined`, and a child fact can never be cleaner than its dirtiest
parent.

We measured it on a synthetic corpus: 10 payloads × 3 channels (memory, tool,
skill) × 3 rounds, plus 20 benign tasks.

| mode | round 1 | round 2 | round 3 | utility | false denial |
|---|---|---|---|---|---|
| baseline | 100% | 100% | 100% | 100% | 0% |
| filter only | 0% | 10% | 0% | 100% | 0% |
| taint + antibodies | **0%** | **0%** | **0%** | **100%** | **0%** |

The interesting row is the middle one. A pure filter stops the original
payloads, then a reworded variant slips through in round 2. The antibody
memory closes that gap in the next round, at roughly 1.3 milliseconds per
check. A harder reference corpus measured 3.3% → 0% → 0% and 1.55 ms.

This is not a claim that prompt injection is solved. It is a claim that the
defense should improve with every attack, and that the improvement should be
measured alongside utility and false denials.

## 3. Honesty: measure the claim, not the answer

The third component came from a different embarrassment. An agent controlling
several machines reported success for a program that did not exist. The
machine had returned `ok:true` with "timed out" in the error field. Another
reported success for an Android package that was not installed. A third
executed a GUI action in a session with no desktop.

Text benchmarks would score all three as passes. `crossnode-bench` compares
each node's claim with ground truth and records **false success** as its own
metric. In the demo, two nodes lie and a naive scorer reports 48/48; the
benchmark reports 46/48 and names both lies. On a real Windows/Linux/Android
fleet, the same three classes reproduced.

This is the most under-measured property in the agent ecosystem. Demos run on
one machine, with one happy path, and a human reading the output. Production
runs on a fleet, with timeouts, sessions, and actions that silently do
nothing. If your benchmark cannot detect a lie, it is measuring fluency.

## What we learned

Two findings surprised us.

First, **isolation is a spectrum, and the cheapest level is often enough**.
The same task can run under bubblewrap (~81 ms p50), runc (~378 ms), a
seccomp-filtered container (~347 ms), or remote gVisor. Pricing the levels
makes the trade-off explicit instead of arguing about "sandboxing" in the
abstract.

Second, **automatic hardening overfits unless you hold something out**. A
genetic search reduced a seccomp allowlist from 48 to 28 syscalls in 21
seconds while the target task still passed 5/5. It had also removed `brk`,
and the probe crashed with SIGSEGV. Fitness on the target task alone is not
fitness. Every mutation needs a held-out probe set before it is accepted.
That lesson generalizes far beyond seccomp.

## Limitations

The injection corpus is synthetic. An adaptive attacker who knows the patterns
is not covered. Near-miss matching is lexical; a paraphrase with different
vocabulary is not caught until a human or a classifier adds an antibody.
Long benign documents that share vocabulary with an attack can cause false
positives. `proofgate` verifies predicates, not semantic truth — "the customer
is happy" must be decomposed into measurable observations. The cross-node demo
uses mocked lying nodes; the reference fleet run is real but sanitized. Harness
benchmarks are small-N and single-model. None of this is a SOTA claim.

## Reproduce it

```bash
git clone <repo>
cd evidence-first-agent-runtime
./repro.sh
```

No keys, no network, no database. 54 tests across the three components. The
raw evaluation JSON and the claims ledger are in the repository.

If you run agents against real machines, the most useful thing you can send us
is a false positive from the near-miss matcher, or a false success our
benchmark missed. That is how the measurement gets better.

*The agent should be able to say: I could not confirm that. That sentence is
worth more than a thousand confident ones.*
