"""gamAI Trust Layer: verify claims, remember refusals, score false success."""
from .core import (
    ROOT,
    add_antibody,
    check_injection,
    crossnode,
    demo,
    immunity,
    immunity_stats,
    proofgate,
    trust_store,
    verify_claims,
    verify_report,
)

__version__ = "0.2.0"
__all__ = [
    "ROOT", "proofgate", "immunity", "crossnode",
    "verify_claims", "verify_report", "check_injection",
    "add_antibody", "immunity_stats", "demo", "trust_store",
    "__version__",
]
