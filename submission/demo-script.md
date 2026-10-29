# 2:47 demo — shot list (matches docs/rush_demo_3min.mp4)

| time | shot | message |
|---|---|---|
| 0:00 | title card | gamAI Rush — Blast Radius Zero |
| 0:12 | architecture card | four gates, one ledger |
| 0:30 | live UI, `/health` | executor: docker, network: none, read_only: true |
| 0:45 | 3-step task | plan → sandbox → 10 evidence records, `verify.ok: true` |
| 1:35 | `rm -rf /` | refused before the sandbox |
| 2:00 | `compute 2+2` | confirmed, rc 0, stdout SHA-256 |
| 2:20 | injection text | refused, signature matched |
| 2:35 | evidence card | false success is measured, not hidden |
| 2:47 | outro | live URL + repo |

The recording is from the Vultr instance `rush2` (45.76.91.239:8098) on 29.10.2026.
