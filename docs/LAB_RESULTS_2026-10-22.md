# VastVM lab results — 2026-10-22

Defensive lab only. Host: `ubuntu` (Vast VM, 10 vCPU, 32 GB RAM, GTX 1660 SUPER 6 GB).

## Infrastructure fix

- Docker client/server were mismatched (client 29.1.3, daemon 24.0.7, API 1.43).
- `systemctl restart docker` -> client/server **29.1.3**, API **1.52**; `docker run hello-world` OK.
- Disk: **84% -> 75%**, 6.6 GB -> **9.8 GB free**.
- Removed `/opt/android-sdk` (3.3 GB, reinstallable). Phone code + APK + install logs backed up first:
  `/root/backups/vastvm-phone-20261022.tgz` (4.9 MB) on Contabo.
- Emulator PID 33918 stopped; phone bridge was already dead.

## gVisor checkpoint/restore, n=20

Command: `/opt/p3/A_final2.sh` looped 20 times, with cleanup after each run.

| Metric | Result |
|---|---:|
| runs OK | **20/20** |
| failures | **0** |
| checkpoint p50 / p95 | **24.5 / 26 ms** |
| restore p50 / p95 | **78 / 127 ms** |
| restore min / max | 65 / 127 ms |
| checkpoint image | ~384 KB |

Every run preserved the counter and continued monotonically. This upgrades the
previous n=1 result to a stable 20-run baseline on this host.

## Firecracker snapshot resume, n=20

Command: `/opt/p4/fc_bench.py` four batches (5 resumes per batch).

| Metric | Result |
|---|---:|
| runs OK | **20/20** |
| HTTP load 204 | **20/20** |
| load p50 / p95 | **6.51 / 9.61 ms** |
| total p50 / p95 | **8.80 / 14.28 ms** |
| load min / max | 6.23 / 9.61 ms |

Previous n=5 result is confirmed at n=20. This measures snapshot **load**, not
snapshot creation; the existing `/opt/fc/mem.bin` and `snap.bin` were reused.

## Artifacts

- `/root/gv20_summary.json` (Vast VM): all 20 gVisor records.
- `/opt/p4/fc.json` and `/tmp/fcJ_*.json` (Vast VM): FC batches.
- `/root/backups/vastvm-phone-20261022.tgz` (Contabo): phone backup.

## Limits

- Same host and same kernel for all runs; not an independent reproduction.
- FC snapshot creation still has no artifact; only resume is measured.
- Two older Firecracker VMs were still running; they were not used or killed.
- gVisor restore p95 (127 ms) is ~1.6x p50; tail matters for scheduling.

## Next

1. E1 mutation-widening: 20 benign + 40 malicious variants; 40/40 denied
   before execution, 0 capability gain.
2. Lease-bound proof chain: PROTEAN lease + proofgate report; tamper/replay
   must fail closed.
3. Fix `p5` minimizer reproducibility and run 3 workloads with holdout.
