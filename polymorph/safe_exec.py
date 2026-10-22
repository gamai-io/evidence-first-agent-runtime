#!/usr/bin/env python3
"""Pinned-fd + memfd + pre-exec hash countermeasure (lab only).

Usage:
  safe_exec.py [--ready PATH] [--receipt PATH] [--delay SECONDS] PATH EXPECTED_SHA [ARG...]
"""
from __future__ import annotations

import hashlib
import json
import os
import stat
import sys
import time


def deny(code: str, detail: str = "") -> int:
    print(json.dumps({"ok": False, "executed": False, "denied": code, "detail": detail},
                     sort_keys=True))
    return 126


def read_all(fd: int) -> bytes:
    chunks = []
    while True:
        b = os.read(fd, 65536)
        if not b:
            return b"".join(chunks)
        chunks.append(b)


def main() -> int:
    args = sys.argv[1:]
    ready = None
    receipt = None
    delay = 0.0
    while args and args[0].startswith("--"):
        if args[0] == "--ready":
            args.pop(0)
            ready = args.pop(0)
        elif args[0] == "--delay":
            args.pop(0)
            delay = float(args.pop(0))
        elif args[0] == "--receipt":
            args.pop(0)
            receipt = args.pop(0)
        else:
            return deny("bad_option", args[0])
    if len(args) < 2:
        return deny("usage")
    path, expected = args[0], args[1]
    extra = args[2:]

    # Policy: never resolve through PATH; the caller must pin an absolute path.
    if not os.path.isabs(path):
        return deny("relative_or_path_resolution_denied", path)
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except OSError as exc:
        return deny("open_no_follow_denied", f"{exc.errno}:{exc.strerror}")
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            return deny("not_a_regular_file")
        data = read_all(fd)
    finally:
        os.close(fd)

    got = hashlib.sha256(data).hexdigest()
    if got != expected:
        return deny("pre_exec_hash_mismatch", got)

    # Snapshot the exact admitted bytes into an anonymous inode. Changing the
    # source path after this point cannot change what runs.
    mfd = os.memfd_create("toctou-snapshot", 0)
    os.write(mfd, data)
    os.fchmod(mfd, 0o700)
    os.lseek(mfd, 0, os.SEEK_SET)
    snap = read_all(mfd)
    snap_hash = hashlib.sha256(snap).hexdigest()
    if snap_hash != expected:
        return deny("memfd_hash_mismatch", snap_hash)
    os.set_inheritable(mfd, True)

    if receipt:
        with open(receipt, "w", encoding="utf-8") as fh:
            json.dump({"ok": True, "path": path, "admitted_sha": expected,
                       "executed_sha": snap_hash, "ts": time.time()}, fh, sort_keys=True)

    if ready:
        with open(ready, "w", encoding="utf-8") as fh:
            fh.write(snap_hash)
    if delay:
        time.sleep(delay)

    # Execute the anonymous snapshot, not the path. /bin/sh reads the inherited
    # memfd; this deliberately handles shell payloads only (lab scope).
    os.execve("/bin/sh", ["/bin/sh", f"/proc/self/fd/{mfd}", *extra], os.environ)
    return 127


if __name__ == "__main__":
    raise SystemExit(main())
