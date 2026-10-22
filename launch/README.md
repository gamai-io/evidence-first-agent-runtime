# Launch kit — evidence-first agent runtime

**Status: prepared, NOT published.** Nothing here may be posted until the owner
says **"objavi"** and names the channel. This folder exists so the decision is
one word, not a week of work.

## What ships

| Asset | File | State |
|---|---|---|
| Repos (3) | `../proofgate`, `../agent-immunity`, `../crossnode-bench` | tests green, sanitized |
| One-command repro | `../repro.sh` | works offline |
| Show HN | `hn.md` | draft |
| Product Hunt | `producthunt.md` | draft |
| X thread | `x-thread.md` | draft |
| Reddit | `reddit.md` | draft |
| Blog post | `blog-post.md` | full draft |
| 90-second video | `video-script.md` | shot list |
| Claims ledger | `claims.md` | every number + limitation |
| Sanitization check | `sanitize.sh` | run before every push |

## The one-line pitch

> **Evidence-first agent runtime: every claim carries a proof, every attack
> leaves an antibody, every machine is checked against ground truth.**

## Three money shots (record these first)

1. **Refusal.** Ask the agent to confirm a file exists. Baseline says "done".
   Ours says `refuted` / `unverified` with a SHA-256.
2. **Immunity.** Injection succeeds 10/10 in round 1; after antibodies,
   0/10 in round 3, with the same utility and ~1.3 ms overhead.
3. **Honesty.** Two nodes claim `ok:true`; the benchmark names both lies and
   reports 46/48 instead of 48/48.

## Publish order (when approved)

1. Push the three repos + root README to a **new public org** (suggested:
   `gamai-labs`), MIT, no history from private repos.
2. Tag `v0.1.0`, enable Issues, add a `good first issue` for each repo.
3. Post the blog + video.
4. Show HN (Tue–Thu, 08:00–10:00 ET), then Product Hunt (00:01 PT), then X
   thread, then Reddit (stagger by 2–4 hours; do not spam).
5. Reply to every technical comment for 48 h. Ask for reproduction, not praise.
6. File the grant/incubator updates that reference the public artifacts.

## Rules

- Never mention the company, customers, internal systems, machines, addresses,
  credentials, or private benchmarks.
- Every number is labeled with N and "our corpus/tasks".
- Never claim SOTA. Claim *reproducibility*.
- Credit dependencies and prior art (taint tracking, seccomp, antibody/
  artificial immune systems, SWE-bench-style harnesses).
- Do not publish customer data, screenshots of private dashboards, or keys.

## Definition of done (for the launch)

- [ ] `./repro.sh` green on a clean machine
- [ ] `sanitize.sh` clean
- [ ] 3 repos public, README renders, license present
- [ ] 90-second video uploaded (no private UI in frame)
- [ ] blog live with links to repos
- [ ] HN/PH/X/Reddit posted only after explicit approval
- [ ] issue templates + SECURITY.md present
- [ ] first 10 external reproductions logged
