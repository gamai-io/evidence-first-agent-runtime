"""Sandbox executors.

The agent never touches the host. Commands go to an isolated execution
environment; the default local adapter is Docker with no network, no host
filesystem, a memory cap and a PID cap. The Vultr adapter runs the same
contract on a disposable cloud instance.
"""

from __future__ import annotations

import hashlib
import os
import shlex
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class ExecResult:
    ok: bool
    rc: int
    stdout: str
    stderr: str
    duration_ms: int
    backend: str
    stdout_sha256: str = ""
    stderr_sha256: str = ""

    def __post_init__(self) -> None:
        self.stdout_sha256 = hashlib.sha256(self.stdout.encode("utf-8")).hexdigest()
        self.stderr_sha256 = hashlib.sha256(self.stderr.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "rc": self.rc,
            "stdout": self.stdout[-4000:],
            "stderr": self.stderr[-2000:],
            "duration_ms": self.duration_ms,
            "backend": self.backend,
            "stdout_sha256": self.stdout_sha256,
            "stderr_sha256": self.stderr_sha256,
        }


class Executor(Protocol):
    name: str

    def run(self, command: str, timeout: float = 30.0) -> ExecResult: ...

    def info(self) -> dict: ...


@dataclass
class NullExecutor:
    name: str = "null"
    script: dict[str, str] = field(default_factory=dict)

    def run(self, command: str, timeout: float = 30.0) -> ExecResult:
        started = time.time()
        out = self.script.get(command, "")
        rc = 0 if command in self.script or not self.script else 1
        return ExecResult(rc == 0, rc, out, "" if rc == 0 else "not found", int((time.time() - started) * 1000), self.name)

    def info(self) -> dict:
        return {"backend": self.name}


@dataclass
class DockerExecutor:
    image: str = "python:3.12-slim"
    memory: str = "256m"
    pids_limit: int = 64
    cpus: str = "1.0"
    user: str = ""
    volume: str = ""
    name: str = "docker"

    def available(self) -> bool:
        return shutil.which("docker") is not None

    def run(self, command: str, timeout: float = 30.0) -> ExecResult:
        started = time.time()
        if not self.available():
            return ExecResult(False, 127, "", "docker not available", 0, self.name)
        argv = [
            "docker", "run", "--rm", "-i",
            "--network", "none",
            "--read-only",
            "--tmpfs", "/tmp:rw,exec,nosuid,size=32m",
            "--memory", self.memory,
            "--pids-limit", str(self.pids_limit),
            "--cpus", self.cpus,
            "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges",
        ]
        if self.user:
            argv += ["--user", self.user]
        if self.volume:
            argv += ["-v", f"{self.volume}:/work"]
        argv += [
            self.image,
            "sh", "-lc", command,
        ]
        try:
            proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)
            rc, out, err = proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired:
            rc, out, err = 124, "", f"timeout after {timeout}s"
        return ExecResult(rc == 0, rc, out, err, int((time.time() - started) * 1000), self.name)

    def cleanup(self) -> None:
        if self.volume:
            subprocess.run(["docker", "volume", "rm", "-f", self.volume], capture_output=True, text=True, check=False)

    def info(self) -> dict:
        return {"backend": self.name, "image": self.image, "network": "none", "read_only": True, "volume": self.volume or None}


@dataclass
class SrtExecutor:
    profile: str = "offline"
    name: str = "srt"

    def available(self) -> bool:
        return shutil.which("srt") is not None

    def run(self, command: str, timeout: float = 30.0) -> ExecResult:
        started = time.time()
        if not self.available():
            return ExecResult(False, 127, "", "srt not available", 0, self.name)
        argv = ["srt", "--profile", self.profile, "--", "sh", "-lc", command]
        try:
            proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)
            rc, out, err = proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired:
            rc, out, err = 124, "", f"timeout after {timeout}s"
        return ExecResult(rc == 0, rc, out, err, int((time.time() - started) * 1000), self.name)

    def info(self) -> dict:
        return {"backend": self.name, "profile": self.profile}


@dataclass
class VultrVMExecutor:
    """Runs commands on a disposable Vultr instance over SSH."""

    host: str = ""
    port: int = 22
    user: str = "root"
    key_path: str = ""
    name: str = "vultr-vm"

    def available(self) -> bool:
        return bool(self.host) and shutil.which("ssh") is not None

    def run(self, command: str, timeout: float = 30.0) -> ExecResult:
        started = time.time()
        if not self.available():
            return ExecResult(False, 127, "", "VULTR_HOST not configured", 0, self.name)
        argv = [
            "ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=accept-new",
            "-o", "ConnectTimeout=8", "-p", str(self.port),
        ]
        if self.key_path:
            argv += ["-i", os.path.expanduser(self.key_path)]
        argv += [f"{self.user}@{self.host}", command]
        try:
            proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)
            rc, out, err = proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired:
            rc, out, err = 124, "", f"timeout after {timeout}s"
        return ExecResult(rc == 0, rc, out, err, int((time.time() - started) * 1000), self.name)

    def info(self) -> dict:
        return {"backend": self.name, "host": self.host or "unset", "isolated": True}


def pick_executor() -> Executor:
    mode = os.environ.get("RUSH_EXECUTOR", "auto").lower()
    vm = VultrVMExecutor(
        host=os.environ.get("VULTR_HOST", ""),
        port=int(os.environ.get("VULTR_SSH_PORT", "22")),
        user=os.environ.get("VULTR_SSH_USER", "root"),
        key_path=os.environ.get("VULTR_SSH_KEY", ""),
    )
    if mode == "vultr" and vm.available():
        return vm
    docker = DockerExecutor()
    if mode in ("auto", "docker") and docker.available():
        return docker
    srt = SrtExecutor()
    if mode in ("auto", "srt") and srt.available():
        return srt
    if mode == "vultr":
        return vm
    return NullExecutor()
