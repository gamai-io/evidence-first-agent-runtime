"""Static effect/scope admission for a plan IR.

This is an E1 prototype: it decides whether a plan asks for any capability
outside a signed lease. It does not execute anything.
"""
from __future__ import annotations

import json
import os
import unicodedata
from dataclasses import dataclass, field
from urllib.parse import unquote

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
            return False
        target = os.path.normpath(
            unicodedata.normalize("NFKC", unquote(str(scope))))
        if target == ".." or target.startswith("../"):
            return False
        return any(target == root or target.startswith(root.rstrip("/") + "/")
                   for root in allowed)


SCOPE_KEYS = {"path", "host", "target", "channel"}


def _no_dupes(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("duplicate key: %s" % key)
        out[key] = value
    return out


def loads_strict(text: str):
    return json.loads(text, object_pairs_hook=_no_dupes)


def required(plan: dict) -> list[tuple[str, str | None]]:
    if not isinstance(plan, dict):
        raise ValueError("plan must be an object")
    extra = set(plan) - {"id", "kind", "steps"}
    if extra:
        raise ValueError("unknown plan keys: %s" % sorted(extra))
    steps = plan.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError("steps must be a non-empty list")
    out: list[tuple[str, str | None]] = []
    for step in steps:
        if not isinstance(step, dict):
            raise ValueError("step must be an object")
        extra = set(step) - {"op"} - SCOPE_KEYS
        if extra:
            raise ValueError("unknown step keys: %s" % sorted(extra))
        op = step.get("op")
        if op not in EFFECTS:
            raise ValueError("unknown op: %s" % op)
        scopes = [(k, step[k]) for k in SCOPE_KEYS if k in step]
        if len(scopes) != 1:
            raise ValueError("step must have exactly one scope key")
        out.append((op, scopes[0][1]))
    return out


def check(plan: dict, lease: Lease) -> dict:
    reasons: list[str] = []
    caps: list[str] = []
    effects: list[str] = []
    try:
        effects = sorted({e for e, _ in required(plan)})
    except ValueError as exc:
        return {"id": plan.get("id") if isinstance(plan, dict) else None,
                "allow": False, "reasons": ["schema:%s" % exc],
                "capability_gain": [], "effects": []}
    for effect, scope in required(plan):
        if not lease.permits(effect, scope):
            reasons.append("%s:%s" % (effect, scope or "*"))
            caps.append(effect)
    return {
        "id": plan.get("id"),
        "allow": not reasons,
        "reasons": reasons,
        "capability_gain": sorted(set(caps)),
        "effects": effects,
    }
