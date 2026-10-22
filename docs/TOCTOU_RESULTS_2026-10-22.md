# TOCTOU — admitted bytes vs executed bytes (2026-10-22)

E2 binds a lease, report and evidence with HMAC, but that does not prove the
bytes executed are the bytes admitted. Five benign local vectors were tested:

| Vector | Current check | Caught before exec? |
|---|---|---|
| symlink swap | ALLOW | **no** |
| PATH swap | ALLOW | **no** |
| hardlink/inode swap | ALLOW | **no** |
| second download / 302 | ALLOW | **no** |
| rewrite between hash and exec | ALLOW | **no** |

Admitted vs executed SHA-256 differed in every case. An honest report generated
from actual bytes is rejected (`cmd_mismatch`), but only **after** execution.
`lease_proof.py` compares `report.cmd_sha` to `lease.cmd_sha`; it never observes
the executed fd.

## Countermeasure prototype

`polymorph/safe_exec.py`:

- absolute path only, no PATH resolution
- `O_RDONLY|O_NOFOLLOW`
- hash from the open fd, pre-exec compare
- copy to `memfd`, re-hash
- execute the memfd snapshot (`/bin/sh /proc/self/fd/N`)

All five vectors deny: symlink `open_no_follow_denied`, PATH
`relative_or_path_resolution_denied`, hardlink/download/rewrite
`pre_exec_hash_mismatch`. Snapshot race: source rewritten after the memfd
snapshot still executed `SAFE`.

## Limits

- Shell-script scope only; ELF needs `execveat(AT_EMPTY_PATH)`.
- Lease still does not bind `argv`, `cwd`, env, interpreter or shared libraries.
- `O_NOFOLLOW` protects the last component only; use `openat2` with
  `RESOLVE_BENEATH|RESOLVE_NO_SYMLINKS` for roots.
- Not tested under gVisor/bwrap seccomp.

## Next

Sign `argv` (no shell string), cwd and env; execute only a pinned fd; build
`cmd_sha` from the executor snapshot, not from the plan.
