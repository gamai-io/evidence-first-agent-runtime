# LabLab submission — copy/paste

**Title**
rush — Blast Radius Zero: an agent that proves what it did

**Tagline (≤120)**
A containment-first web agent: it plans, runs every command inside a Vultr sandbox, and accepts a result only when the sandbox proves it.

**Short description (≤600)**
Most agents claim "done". rush proves it. Every task is planned, each command passes a destructive/injection guard before execution, runs inside an isolated Docker sandbox on a Vultr VM (no network, read-only root, cap-drop, memory/PID limits), and the result is accepted only if the exit code and SHA-256 of stdout are chained into a tamper-evident ledger. Anything unproven is reported as unverified — the agent fails closed, not silently.

**Long description**
Problem: autonomous agents now execute code and shell commands. The dangerous failure is not being wrong — it is being confidently wrong: reporting a task as done when nothing ran, or running a destructive command because an instruction was injected into the context.

What we built — four gates:
1. Guard, before planning and before execution: refuses destructive commands (rm -rf, mkfs, dd to /dev, drop table, shutdown) and prompt-injection patterns; the refusal is recorded.
2. Planner: turns the task into explicit steps with a reason per step (deterministic by default, Vultr Serverless Inference optional).
3. Sandbox executor: every command runs in a container on a Vultr instance — `--network none`, `--read-only`, `cap-drop ALL`, memory/PID limits, per-run volume. Disposable: the sandbox is the blast radius.
4. Evidence ledger: exit code + SHA-256(stdout) + SHA-256(stderr) per step, chained; `verify` detects tampering. A claim is accepted only with matching evidence, otherwise `unverified`.

Why it fits the challenge: it is a production-style web app, it does real work (not a simulation), and it measures containment and honesty with reproducible numbers.

Vultr usage: Vultr Cloud Compute (vc2-1c-1gb, fra) runs the app and the Docker sandbox; `deploy_vultr.sh` + `deploy_rush.sh` provision it. Vultr Serverless Inference is optional for planning.

**Tech / tags**
Python, FastAPI, Docker, Vultr Cloud Compute, Vultr Serverless Inference, SHA-256 evidence chain, prompt-injection guard, sandboxing, AI agents, security

**Links**
- Live app: http://45.76.91.239:8098/
- Repo: https://github.com/gamai-io/evidence-first-agent-runtime
- App source: https://github.com/gamai-io/evidence-first-agent-runtime/tree/main/rush
- Demo video (2:47): https://github.com/gamai-io/evidence-first-agent-runtime/raw/main/docs/rush_demo_3min.mp4
- Blog (BS): https://gamai.io/blog/evidence-first-agent-runtime.html

**Video**
2:47, recorded from the live Vultr UI: benign 3-step run (10 evidence records, verify ok), destructive refusal, injection refusal, health endpoint, simple confirmed run.

**Reproduce**
```bash
git clone https://github.com/gamai-io/evidence-first-agent-runtime
cd evidence-first-agent-runtime
python -m pytest rush/tests -q          # 6 passed
python -m uvicorn rush.app:app --port 8098
```
