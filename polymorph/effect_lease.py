"""Static effect/scope admission for a plan IR.

This is an E1 prototype: it decides whether a plan asks for any capability
outside a signed lease. It does not execute anything.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

EFFECTS = ("fs.read", "fs.write", "net.connect", "exec", "db.read", "send")


@dataclass(frozen=True)
class Lease:
    effects: dict[str, tuple[str, ...]] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "Lease":
        out: dict[str, tuple[str, ...]] = {}
        for key, scopes in (data.get("effects") or {}).items():
            if key not in EFFECTS:
                raise ValueError("unknown effect: %s" % key)
            out[key] = tuple(os.path.normpath(str(s)) for s in (scopes or ()))
        return cls(out)

    def permits(self, effect: str, scope: str | None) -> bool:
        if effect not in self.effects:
            return False
        allowed = self.effects[effect]
        if not allowed:
            return False
        if scope is None:
            return True
        target = os.path.normpath(str(scope))
        if target == ".." or target.startswith("../"):
            return False
        return any(target == root or target.startswith(root.rstrip("/") + "/")
                   for root in allowed)


def required(plan: dict) -> list[tuple[str, str | None]]:
    out: list[tuple[str, str | None]] = []
    for step in plan.get("steps", []):
        op = step.get("op")
        if op not in EFFECTS:
            raise ValueError("unknown op: %s" % op)
        scope = step.get("path") or step.get("host") or step.get("target") or step.get("channel")
        out.append((op, scope))
    return out


def check(plan: dict, lease: Lease) -> dict:
    reasons: list[str] = []
    caps: list[str] = []
    for effect, scope in required(plan):
        if not lease.permits(effect, scope):
            reasons.append("%s:%s" % (effect, scope or "*"))
            caps.append(effect)
    return {
        "id": plan.get("id"),
        "allow": not reasons,
        "reasons": reasons,
        "capability_gain": sorted(set(caps)),
        "effects": sorted({e for e, _ in required(plan)}),
    }
