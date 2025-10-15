import importlib.util
import os
from pathlib import Path


def load_env_module():
    path = Path("src/part1/1-3-1_environment_setup.py")
    spec = importlib.util.spec_from_file_location("env_setup", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def test_setup_environment_missing_key_returns_false(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    # Ensure no GOOGLE_API_KEY present
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    mod = load_env_module()
    ok = mod.setup_streaming_environment()
    assert ok is False


def test_setup_environment_with_key_returns_true(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key-12345678")
    mod = load_env_module()
    ok = mod.setup_streaming_environment()
    assert ok is True


def test_create_sample_env_file(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    mod = load_env_module()
    mod.create_sample_env_file()
    env_example = Path(".env.example")
    assert env_example.exists()
    text = env_example.read_text()
    assert "GOOGLE_API_KEY" in text

