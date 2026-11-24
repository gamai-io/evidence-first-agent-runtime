import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from rush import llm


def test_nim_unavailable_without_key(monkeypatch):
    monkeypatch.delenv("NVIDIA_NIM_API_KEY", raising=False)
    nim = llm.NvidiaNim(api_key="")
    assert nim.available() is False
    assert nim.name == "nvidia-nim"


def test_nim_available_with_key():
    nim = llm.NvidiaNim(api_key="nvapi-test")
    assert nim.available() is True


def test_nim_defaults_are_openai_compatible():
    nim = llm.NvidiaNim(api_key="nvapi-test")
    assert nim.base.startswith("https://")
    assert not nim.base.endswith("/")
    assert nim.model


def test_build_planner_prefers_nim(monkeypatch):
    monkeypatch.setenv("NVIDIA_NIM_API_KEY", "nvapi-test")
    monkeypatch.setenv("VULTR_INFERENCE_KEY", "vultr-test")
    assert llm.build_planner().name == "nvidia-nim"


def test_build_planner_falls_back_to_vultr(monkeypatch):
    monkeypatch.delenv("NVIDIA_NIM_API_KEY", raising=False)
    monkeypatch.setenv("VULTR_INFERENCE_KEY", "vultr-test")
    assert llm.build_planner().name == "vultr-inference"


def test_plan_falls_back_to_deterministic(monkeypatch):
    monkeypatch.delenv("NVIDIA_NIM_API_KEY", raising=False)
    monkeypatch.delenv("VULTR_INFERENCE_KEY", raising=False)
    steps, origin = llm.plan("list the largest files")
    assert origin == "deterministic"
    assert steps
