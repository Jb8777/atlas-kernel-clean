from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from core.config_loader import get_model_for_route, load_json_config

# ── get_model_for_route ───────────────────────────────────────────────────────


def test_get_model_for_route_returns_config_value(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Model names from config/model_router.json are returned per route."""
    cfg = tmp_path / "model_router.json"
    cfg.write_text(
        json.dumps(
            {
                "models": {
                    "code": "openai/gpt-4o",
                    "research": "openai/gpt-4o",
                    "ops": "openai/gpt-4o",
                    "general": "openai/gpt-3.5-turbo",
                }
            }
        )
    )
    monkeypatch.setenv("CONFIG_PATH", str(cfg))
    # Clear lru_cache so monkeypatched env is picked up
    from core.config_loader import get_settings, load_json_config
    get_settings.cache_clear()

    assert get_model_for_route("code") == "openai/gpt-4o"
    assert get_model_for_route("general") == "openai/gpt-3.5-turbo"

    get_settings.cache_clear()


def test_get_model_for_route_missing_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Falls back to default model when config file is absent."""
    monkeypatch.setenv("CONFIG_PATH", str(tmp_path / "nonexistent.json"))
    from core.config_loader import get_settings
    get_settings.cache_clear()

    result = get_model_for_route("code")
    assert isinstance(result, str)
    assert result  # non-empty fallback

    get_settings.cache_clear()


def test_get_model_for_route_unknown_route_returns_default(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An unrecognised route key falls back to the default model."""
    cfg = tmp_path / "model_router.json"
    cfg.write_text(json.dumps({"models": {"code": "openai/gpt-4o"}}))
    monkeypatch.setenv("CONFIG_PATH", str(cfg))
    from core.config_loader import get_settings
    get_settings.cache_clear()

    result = get_model_for_route("does_not_exist")
    assert result == "openai/gpt-3.5-turbo"

    get_settings.cache_clear()


def test_get_model_for_route_malformed_models_section(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A non-dict models section falls back gracefully."""
    cfg = tmp_path / "model_router.json"
    cfg.write_text(json.dumps({"models": "not-a-dict"}))
    monkeypatch.setenv("CONFIG_PATH", str(cfg))
    from core.config_loader import get_settings
    get_settings.cache_clear()

    result = get_model_for_route("code")
    assert result == "openai/gpt-3.5-turbo"

    get_settings.cache_clear()


# ── load_json_config ──────────────────────────────────────────────────────────


def test_load_json_config_returns_empty_for_missing_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONFIG_PATH", str(tmp_path / "missing.json"))
    from core.config_loader import get_settings
    get_settings.cache_clear()

    result = load_json_config()
    assert result == {}

    get_settings.cache_clear()


def test_load_json_config_returns_empty_for_invalid_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = tmp_path / "bad.json"
    cfg.write_text("{not valid json")
    monkeypatch.setenv("CONFIG_PATH", str(cfg))
    from core.config_loader import get_settings
    get_settings.cache_clear()

    result = load_json_config()
    assert result == {}

    get_settings.cache_clear()
