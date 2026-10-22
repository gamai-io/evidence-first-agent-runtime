# 14-day publishing plan

Assumes approval on D0. Nothing is posted before the explicit "objavi".

## D1 — freeze and verify
- Clean generated files (`__pycache__`, `*.db`, `runs/`).
- Run `./repro.sh` twice on a clean machine; record both hashes.
- Run `launch/sanitize.sh`; fix every hit.
- Create `SECURITY.md` + issue templates in each repo.

## D2 — repositories
- Create public org `gamai-io` (or the owner's choice).
- Push `proofgate`, `agent-immunity`, `crossnode-bench` as separate repos, and
  the root as `evidence-first-agent-runtime`.
- Tag `v0.1.0`; add one `good first issue` per repo.
- Confirm README renders and license is detected.

## D3 — video
- Record the three money shots (refusal, memory, false success).
- 90 seconds, captions, no private UI, no machine names.
- Upload (YouTube unlisted first), embed in the blog.

## D4 — blog
- Publish `blog-post.md` with links to repos and video.
- Add a short "reproduce" section at the top.

## D5 — Show HN
- Post 08:00–10:00 ET, Tue–Thu.
- Stay in the thread for 6 hours; answer every technical question.
- Ask for reproduction, not upvotes.

## D6 — Product Hunt
- 00:01 PT. First comment ready.
- Post the video + 3 GIFs (refusal, memory, false success).
- Reply to every comment within 2 hours.

## D7 — X thread + LinkedIn
- Post the 9-tweet thread with the video.
- LinkedIn: longer-form version of the blog, tag open-source, no hype.

## D8 — Reddit
- r/LocalLLaMA (technical), r/AI_Agents (workflow), r/netsec (immunity).
- Stagger 2–4 hours; answer criticism with data, not defensiveness.
- Do not cross-post identical text; adapt each.

## D9 — developer channels
- Discord: OpenCode, MCP, LocalLLaMA.
- `awesome-*` lists and MCP registry.
- dev.to mirror with canonical link.

## D10 — paper/preprint
- arXiv draft: learned antibodies + false-success benchmark + seccomp holdout
  finding. Include raw eval JSON, limitations, and ethics statement.

## D11 — grants and support
- Update Sovereign Tech Fund / EIC / NLnet / OpenSSF with public links.
- NLnet/NGI Zero is the best fit for the immunity + isolation work.
- Enable GitHub Sponsors; add a "support" section to the root README.

## D12 — design partners
- 10 target teams running agents on real machines.
- Offer: a 30-minute integration, a false-positive/false-success report back.

## D13 — measure the launch
- Count external reproductions, issues, false positives, inbound.
- Publish a short "what we learned from the launch" post (numbers only).

## D14 — decide
- If ≥10 external reproductions and ≥3 design partners: double down, ship the
  isolation ladder as the next component.
- If not: fix the onboarding friction first; do not add features.

## Guardrails
- No customer/internal data, ever.
- No SOTA claims.
- One number = one command + one limitation.
- If a claim is challenged and we cannot reproduce it, retract it publicly.
