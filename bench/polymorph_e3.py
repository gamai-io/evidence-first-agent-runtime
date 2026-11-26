#!/usr/bin/env python3
"""Run polymorph's E3 cross-language probe on the installed package.

Upstream ``e3_cross_language.py`` loads its lexical detector with
``sys.path.insert(0, HERE / "agent-immunity")`` and ``import immunity``. In this
umbrella ``agent-immunity/`` is a component of its own, not part of the
polymorph wheel (the two copies are byte-identical at the pinned commits), so
the vendored copy needed a path fix: ``HERE.parent / "agent-immunity"``.

That adaptation lives here now. We put the umbrella's ``agent-immunity/`` on
``sys.path`` and run the installed module as ``__main__``; upstream's own insert
points at a non-existent directory inside site-packages and is inert.

    python3 bench/polymorph_e3.py
"""
from __future__ import annotations

import pathlib
import runpy
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "agent-immunity"))

runpy.run_module("e3_cross_language", run_name="__main__")
