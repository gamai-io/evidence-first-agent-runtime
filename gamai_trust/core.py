"""Public Python API for the three trust components.

The component scripts stay where they are (proofgate/, agent-immunity/,
crossnode-bench/) so that ``./repro.sh`` keeps working. This module loads them
by path, which is enough for a checkout or ``pip install -e .``.

Set GAMAI_TRUST_ROOT if the components live somewhere else.
"""
from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(os.environ.get("GAMAI_TRUST_ROOT", Path(__file__).resolve().parent.parent))
_STORE = None


def _load(name: str, relative: str):
    path = ROOT / relative
    if not path.exists():
        raise FileNotFoundError(
            "cannot find %s; run from the repo or set GAMAI_TRUST_ROOT" % path
        )
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError("cannot load %s" % path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


proofgate = _load("gamai_proofgate", "proofgate/proofgate.py")
immunity = _load("gamai_immunity", "agent-immunity/immunity.py")
crossnode = _load("gamai_crossnode", "crossnode-bench/crossnode.py")


def trust_store():
    """Process-wide antibody store (SQLite). Override with GAMAI_TRUST_DB."""
    global _STORE
    if _STORE is None:
        path = os.environ.get("GAMAI_TRUST_DB") or str(
            Path.home() / ".gamai" / "trust.db"
        )
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        _STORE = immunity.Store(path)
    return _STORE


def verify_claims(claims: list[dict], reported_hash: str | None = None) -> dict:
    """Evaluate claims and return an evidence-bound proofgate report."""
    return proofgate.check(claims or [], reported_hash=reported_hash)


def verify_report(report: dict) -> dict:
    """Recompute the SHA-256 of a previously emitted report."""
    return proofgate.verify(report or {})


def check_injection(text: str, tool: str | None = None) -> dict:
    """Return allow/block plus class, risk and normalized hash."""
    return trust_store().shield_check(text, tool=tool)


def add_antibody(text: str, attack_class: str, reason: str = "mcp",
                 severity: str = "high") -> dict:
    """Turn a blocked sample into a durable antibody signature."""
    return trust_store().antibody_add(reason, attack_class, text, severity)


def immunity_stats() -> dict:
    return trust_store().stats()


def demo() -> dict[str, Any]:
    """Run all three components. Safe to call from a tool or a test."""
    out: dict[str, Any] = {}
    try:
        out["proofgate"] = proofgate.demo()
    except Exception as exc:  # pragma: no cover - defensive
        out["proofgate"] = {"ok": False, "error": str(exc)}

    try:
        tmp = tempfile.mkdtemp(prefix="gamai-trust-")
        store = immunity.Store(os.path.join(tmp, "immunity.db"))
        out["immunity"] = immunity.selftest(store=store)
    except Exception as exc:  # pragma: no cover
        out["immunity"] = {"ok": False, "error": str(exc)}

    try:
        out["crossnode"] = crossnode.run_suite(
            crossnode.demo_nodes(), runs=1,
            outdir=tempfile.mkdtemp(prefix="gamai-crossnode-"),
        )
    except Exception as exc:  # pragma: no cover - platform dependent
        out["crossnode"] = {"ok": False, "error": str(exc)}
    return out


__all__ = [
    "ROOT", "proofgate", "immunity", "crossnode",
    "verify_claims", "verify_report", "check_injection",
    "add_antibody", "immunity_stats", "demo", "trust_store",
]
