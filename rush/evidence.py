"""Tamper-evident evidence ledger.

Every action an agent takes is a claim. This module records each claim with a
SHA-256 hash chained to the previous record, so removing or editing a record
breaks verification.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, asdict
from typing import Any


def canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class Record:
    seq: int
    ts: float
    kind: str
    action: str
    params: dict[str, Any]
    ok: bool
    detail: dict[str, Any]
    prev: str
    digest: str


class Ledger:
    def __init__(self, run_id: str) -> None:
        self.run_id = run_id
        self.records: list[Record] = []
        self._head = sha256_text(run_id)

    @property
    def head(self) -> str:
        return self._head

    def append(
        self,
        kind: str,
        action: str,
        params: dict[str, Any] | None = None,
        ok: bool = True,
        detail: dict[str, Any] | None = None,
    ) -> Record:
        payload = {
            "run": self.run_id,
            "seq": len(self.records) + 1,
            "ts": round(time.time(), 6),
            "kind": kind,
            "action": action,
            "params": params or {},
            "ok": ok,
            "detail": detail or {},
            "prev": self._head,
        }
        digest = sha256_text(canonical(payload))
        rec = Record(
            seq=payload["seq"],
            ts=payload["ts"],
            kind=kind,
            action=action,
            params=payload["params"],
            ok=ok,
            detail=payload["detail"],
            prev=self._head,
            digest=digest,
        )
        self.records.append(rec)
        self._head = digest
        return rec

    def verify(self) -> dict[str, Any]:
        head = sha256_text(self.run_id)
        for index, rec in enumerate(self.records, start=1):
            if rec.seq != index:
                return {"ok": False, "at": index, "reason": "sequence gap"}
            if rec.prev != head:
                return {"ok": False, "at": index, "reason": "broken link"}
            payload = {
                "run": self.run_id,
                "seq": rec.seq,
                "ts": rec.ts,
                "kind": rec.kind,
                "action": rec.action,
                "params": rec.params,
                "ok": rec.ok,
                "detail": rec.detail,
                "prev": rec.prev,
            }
            if sha256_text(canonical(payload)) != rec.digest:
                return {"ok": False, "at": index, "reason": "digest mismatch"}
            head = rec.digest
        return {"ok": True, "count": len(self.records), "head": head}

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "records": [asdict(r) for r in self.records],
            "verify": self.verify(),
        }
