# rush — Blast Radius Zero (web app)

A production-style web app for the **Vultr: Agent Rush** hackathon: it plans a task,
dispatches every command into an isolated sandbox, and returns output that is only
accepted when the sandbox itself proves it (exit code + SHA-256 of stdout), all
chained into a tamper-evident ledger.

**Live demo (Vultr):** http://45.76.91.239:8098/ — Docker executor (`--network none`,
read-only root, cap-drop, memory/PID limits) on a Vultr `vc2-1c-1gb` instance in `fra`.
`deploy_vultr.sh up` provisions the instance; `gama-rush.service` runs the app.

```
task ──► guard ──► planner ──► guard ──► sandbox ──► verify ──► evidence chain
          │                     │            │            │
   injection refusal     command refusal   Vultr/Docker  proofgate
```

## Run locally

```bash
pip install fastapi uvicorn          # web layer only; core is stdlib
python -m uvicorn rush.app:app --port 8098
# open http://127.0.0.1:8098
```

Executor selection (`RUSH_EXECUTOR`):

| value | behaviour |
|---|---|
| `auto` (default) | Vultr VM if configured → Docker → srt → null |
| `docker` | Docker, `--network none`, read-only root, caps dropped, memory/PID caps, `/work` volume |
| `srt` | Anthropic sandbox-runtime profile (`offline`) when available |
| `vultr` | SSH into a disposable Vultr instance (`VULTR_HOST`, `VULTR_SSH_PORT`, `VULTR_SSH_USER`, `VULTR_SSH_KEY`) |

Planner: **Vultr Serverless Inference** when `VULTR_INFERENCE_KEY` is set
(`VULTR_MODEL`, `VULTR_INFERENCE_BASE`), otherwise a deterministic planner so the
demo works offline and never depends on a network.

## API

| method | path | purpose |
|---|---|---|
| GET | `/` | single-page UI |
| GET | `/health` | executor that would be used |
| POST | `/api/run` | run a task, return full result + ledger |
| GET | `/api/run/stream?task=…` | SSE stream of plan, steps, refusals, ledger |

Example:

```bash
curl -s -X POST localhost:8098/api/run -H 'Content-Type: application/json' \
  -d '{"task":"Pronađi 3 najveća fajla, izračunaj SHA-256 i vrati CSV"}'
```

## What is proven

- every executed command has `rc`, duration, stdout hash and is appended to a
  SHA-256 hash chain (`evidence.py`), verified at the end of the run;
- `report` comes from `proofgate.check()` — `confirmed` only if all `rc_zero`
  claims hold, `refuted` otherwise;
- a destructive command or an injected instruction never reaches the sandbox:
  the guard refuses first and the refusal is recorded as evidence.

## Tests

```bash
python -m pytest rush/tests -q     # 6 tests: guard, chain tamper, agent, injection
```
