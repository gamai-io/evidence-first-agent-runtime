#!/usr/bin/env python3
"""Fleet node adapters for the installed ``crossnode-bench`` package.

These two adapters used to live inside the vendored copy of ``crossnode.py``
(``FleetNode`` and ``CliNode``), which meant every upgrade of the benchmark had
to re-apply them. They are umbrella code, not benchmark code, so they live here
now and subclass the installed ``crossnode.Node``:

* ``FleetNode``  — POST ``{"cmd": ..., "to": target}`` to the GAMA fleet bridge.
* ``CliNode``    — ``gama --json hc <target> shell <cmd>``.

``load_config`` mirrors the benchmark's own JSON loader and adds the two extra
node types (``gama-cli``, ``fleet``) the vendored copy accepted. Nothing else
about the benchmark changes: tasks, scoring and evidence are upstream's.

Requires the pinned package: ``pip install -r requirements-vendored.txt``.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

from crossnode import HTTPNode, LocalNode, Node


@dataclass
class FleetNode(Node):
    """HTTP fleet bridge node: POST {"cmd": ..., "to": target}."""
    name: str
    url: str
    target: str
    token: str = ""
    token_env: str = "FLEET_TOKEN"
    probe: str = "all"
    prefix: str = "shell "

    def run(self, cmd: str, timeout: int = 25) -> dict:
        body = json.dumps({"cmd": self.prefix + cmd, "to": self.target}).encode()
        headers = {"Content-Type": "application/json"}
        token = self.token or os.environ.get(self.token_env, "")
        if token:
            headers["X-Token"] = token
        req = urllib.request.Request(self.url, data=body, method="POST", headers=headers)
        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read(2 * 1024 * 1024).decode("utf-8", "replace"))
        except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
            return {"ok": False, "rc": 124, "out": "", "err": str(exc)[:400],
                    "ms": round((time.perf_counter() - t0) * 1000, 1)}
        item = (data.get("results") or {}).get(self.target, data)
        item.setdefault("ms", round((time.perf_counter() - t0) * 1000, 1))
        item.setdefault("rc", 0 if item.get("ok") else 1)
        return item


@dataclass
class CliNode(Node):
    """Use the `gama --json hc <target> shell <cmd>` CLI path."""
    name: str
    target: str = ""
    probe: str = "all"
    timeout: int = 30

    def run(self, cmd: str, timeout: int = 25) -> dict:
        t0 = time.perf_counter()
        try:
            proc = subprocess.run(["gama", "--json", "hc", self.target or self.name,
                                   "shell " + cmd], capture_output=True, text=True,
                                  timeout=max(timeout, self.timeout))
            data = json.loads(proc.stdout.strip().splitlines()[-1])
            data.setdefault("ms", round((time.perf_counter() - t0) * 1000, 1))
            data.setdefault("rc", 0 if data.get("ok") else 1)
            return data
        except Exception as exc:
            return {"ok": False, "rc": 124, "out": "", "err": str(exc)[:400],
                    "ms": round((time.perf_counter() - t0) * 1000, 1)}


def load_config(path: str) -> list[Node]:
    """Load a node config, accepting the benchmark's types plus gama-cli/fleet."""
    with open(path, encoding="utf-8") as fh:
        cfg = json.load(fh)
    nodes: list[Node] = []
    for item in cfg.get("nodes", []):
        kind = item.get("type")
        if kind == "local":
            nodes.append(LocalNode(item.get("name", "local")))
        elif kind == "http":
            nodes.append(HTTPNode(item["name"], item["url"],
                                  token_env=item.get("token_env", "NODE_TOKEN")))
        elif kind == "gama-cli":
            nodes.append(CliNode(item.get("name", item.get("target", "node")),
                                 item.get("target", item.get("name"))))
        elif kind == "fleet":
            nodes.append(FleetNode(item.get("name", item.get("target", "fleet")),
                                   item["url"], item.get("target", item.get("name")),
                                   token_env=item.get("token_env", "FLEET_TOKEN"),
                                   prefix=item.get("prefix", "shell ")))
        else:
            raise SystemExit("unknown node type: %r" % kind)
    return nodes
