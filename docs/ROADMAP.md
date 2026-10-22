# Roadmap

The goal is narrow: make **agent claims verifiable** — not another agent framework.

## Principles

1. **Evidence before assertion.** A claim is `confirmed`, `refuted`, or `unverified`; never silently promoted.
2. **Fail closed.** Missing, malformed, or tampered evidence is not a pass.
3. **Measure false success.** A benchmark that cannot detect a lying agent is not a benchmark.
4. **Small, local, inspectable.** No mandatory cloud, no hidden model, no vendor lock-in.
5. **Open conformance.** Anyone can run the tests and publish a result.

## v0.2 — Q4 2026

- **Acknowledgement contract** for remote actions: `ok: true` only after the effect is verified; timeout and missing target are failures.
- **GitHub Action** `trust-gate`: verify claims/evidence in CI; fail the job on `refuted` or tampered evidence.
- **Held-out benchmark v2**: 150 realistic tasks, published `tasks.json`, seeds, runner, and per-category results.
- **Conformance document** with testable requirements and a badge for implementations.
- **Security hygiene**: signed releases, SBOM, dependency and secret checks in CI.

## v0.3 — Q1 2027

- **Signed evidence envelope** (Ed25519) as a stable format, with a CLI `verify` command.
- **Policy specification** for allow/deny decisions, with deny precedence and fail-closed defaults.
- **Marketplace manifest verification**: hash + signature + expected files; no execution.
- **Agent team runtime**: per-agent memory scope and isolated worktrees.

## v1.0 — 2027

- **Conformance program**: independent runs, published results, public badge.
- **Integrations** with common agent runtimes and CI systems.
- **Second vertical**: consent-aware telephony (`ConsentLedger`) as an open evidence format.

## Non-goals

- A new foundation model.
- A general-purpose agent framework.
- A hosted SaaS that holds customer data.
- Claims of “AGI safety” or “100% secure”. We measure specific failure modes and publish limits.

## How to contribute

- Run `./repro.sh` and open an issue with the exact output.
- Add a failing case to `bench/` before changing behaviour.
- Keep the public core dependency-free; optional integrations live behind extras.
- Do not include customer data, credentials, or internal hostnames in issues or PRs.

## Status

See [README](../README.md), [Architecture](ARCHITECTURE.md), [Threat model](THREAT_MODEL.md), and [Evidence index](EVIDENCE.md).
