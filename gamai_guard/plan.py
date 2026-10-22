from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "polymorph"))
from effect_lease import Lease, check, loads_strict  # noqa: E402,F401

__all__ = ["Lease", "check", "loads_strict"]
