from __future__ import annotations

import hashlib
import hmac
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

RISK_RE = re.compile(
    r"\b(rm\s+-rf|obrisi|izbrisi|delete|drop\s+table|drop\s+database|truncate|"
    r"shutdown|reboot|kill|pkill|chmod|chown|/etc/|/var/log|\.ssh|passwd|password|"
    r"api[ _-]?key|token|secret|system prompt|ignore .{0,30}instructions|harness|"
    r"shell|fleet|mail|send|whatsapp|exec|sudo)\b", re.I)


def canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def sha(obj) -> str:
    return hashlib.sha256(canon(obj)).hexdigest()


@dataclass
class Proposal:
    intent: str
    goal: str
    evidence: list[str]
    proposer: str
    approver: str = ""
    ok: int = 0
    fail: int = 0
    risk: list[str] = field(default_factory=list)


def evaluate(p: Proposal) -> dict:
    risk = list(p.risk)
    text = (p.intent or "") + " " + (p.goal or "")
    if RISK_RE.search(text):
        risk.append("risky_goal")
    if p.ok < 5 or p.fail != 0:
        risk.append("insufficient_evidence")
    if not p.evidence:
        risk.append("no_effect_evidence")
    if p.proposer == p.approver:
        risk.append("same_principal")
    return {"intent": p.intent, "goal": p.goal, "risk": sorted(set(risk)),
            "ready": not risk, "evidence": p.evidence, "proposer": p.proposer,
            "approver": p.approver, "ok": p.ok, "fail": p.fail}


def sig_for(p: Proposal, key: bytes) -> str:
    body = {"intent": p.intent, "goal": p.goal, "evidence": p.evidence,
            "proposer": p.proposer, "approver": p.approver, "ok": p.ok, "fail": p.fail}
    return hmac.new(key, canon(body), hashlib.sha256).hexdigest()


class ApprovalStore:
    def __init__(self, path: str | Path, key: bytes):
        self.path = Path(path)
        self.key = key
        self.rows: dict[str, dict] = {}
        if self.path.exists():
            try:
                self.rows = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                self.rows = {}

    def approve(self, p: Proposal) -> dict:
        ev = evaluate(p)
        if ev["ready"] is False:
            return {"ok": False, "reasons": ev["risk"]}
        if p.approver == p.proposer:
            return {"ok": False, "reasons": ["same_principal"]}
        row = {"intent": p.intent, "goal": p.goal, "evidence": p.evidence,
               "proposer": p.proposer, "approver": p.approver,
               "sig": sig_for(p, self.key), "ts": time.time()}
        self.rows[p.intent] = row
        self.path.write_text(json.dumps(self.rows, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"ok": True, "intent": p.intent, "sig": row["sig"]}

    def check(self, p: Proposal) -> bool:
        row = self.rows.get(p.intent)
        if not row:
            return False
        return (row.get("approver") != row.get("proposer")
                and hmac.compare_digest(row.get("sig", ""), sig_for(p, self.key)))
