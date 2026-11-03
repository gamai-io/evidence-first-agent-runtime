import hashlib
import json
import os
import time

from .core import canon


class Evidence:
    def __init__(self, path=None):
        self.path = path
        self.records = []
        self.prev_hash = "0" * 64
        if path:
            os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)

    def append(self, record):
        rec = dict(record)
        rec.setdefault("ts", time.time())
        rec["prev_hash"] = self.prev_hash
        h = hashlib.sha256(canon(rec)).hexdigest()
        rec["hash"] = h
        self.prev_hash = h
        self.records.append(rec)
        if self.path:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
        return rec

    def chain_valid(self):
        prev = "0" * 64
        for rec in self.records:
            body = {k: v for k, v in rec.items() if k != "hash"}
            if body.get("prev_hash") != prev:
                return False
            if hashlib.sha256(canon(body)).hexdigest() != rec.get("hash"):
                return False
            prev = rec["hash"]
        return True

    def merkle_root(self):
        hashes = [r["hash"] for r in self.records]
        if not hashes:
            return hashlib.sha256(b"").hexdigest()
        while len(hashes) > 1:
            if len(hashes) % 2:
                hashes = hashes + [hashes[-1]]
            hashes = [hashlib.sha256((hashes[i] + hashes[i + 1]).encode()).hexdigest() for i in range(0, len(hashes), 2)]
        return hashes[0]
