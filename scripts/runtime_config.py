"""Small, non-secret runtime configuration for optional field-search routes.

The core skill remains standard-library-only.  This module only reads a local
JSON file containing path references; it never reads credential stores, cookies,
tokens, or browser data.  A caller may still override every path explicitly.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
from typing import Any


CONFIG_ENV = "FIELD_SEARCH_CONFIG"
DEFAULT_CONFIG_PATH = Path.home() / ".codex" / "field-search" / "config.json"
_SENSITIVE_KEY = re.compile(
    r"(?:token|cookie|secret|password|credential|authorization|api[_-]?key|refresh[_-]?token)",
    re.IGNORECASE,
)


class ConfigError(ValueError):
    """A malformed or unsafe local configuration."""


def selected_config_path(explicit: str | None = None) -> tuple[Path, str]:
    """Return the selected config path and how it was selected."""

    if explicit:
        return Path(explicit).expanduser(), "explicit"
    env_value = os.getenv(CONFIG_ENV)
    if env_value:
        return Path(env_value).expanduser(), "environment"
    return DEFAULT_CONFIG_PATH, "default"


def _validate_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{label}_must_be_nonempty_string")
    if "\x00" in value or "\r" in value or "\n" in value:
        raise ConfigError(f"{label}_contains_control_character")
    return value


def _check_key(key: Any, label: str) -> str:
    key = _validate_string(key, label)
    if _SENSITIVE_KEY.search(key):
        raise ConfigError(f"{label}_looks_sensitive")
    return key


def _validate(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ConfigError("config_must_be_object")
    version = data.get("schema_version", 1)
    if version != 1:
        raise ConfigError("unsupported_config_schema_version")
    for key in data:
        if key not in {"schema_version", "runtimes", "readers"}:
            raise ConfigError("unknown_config_section")
    for section_name in ("runtimes", "readers"):
        section = data.get(section_name, {})
        if not isinstance(section, dict):
            raise ConfigError(f"{section_name}_must_be_object")
        for key, value in section.items():
            _check_key(key, f"{section_name}_key")
            if section_name == "runtimes":
                if isinstance(value, str):
                    _validate_string(value, f"runtime_{key}")
                elif isinstance(value, dict):
                    for nested_key in value:
                        if nested_key != "python_path":
                            raise ConfigError("runtime_entry_only_allows_python_path")
                    _validate_string(value.get("python_path"), f"runtime_{key}_python_path")
                else:
                    raise ConfigError("runtime_entry_must_be_path_or_object")
            else:
                if not isinstance(value, dict):
                    raise ConfigError("reader_entry_must_be_object")
                for nested_key, nested_value in value.items():
                    _check_key(nested_key, f"reader_{key}_key")
                    if nested_key not in {"session_root", "adapter_path", "python_path"}:
                        raise ConfigError("reader_entry_contains_unsupported_field")
                    _validate_string(nested_value, f"reader_{key}_{nested_key}")
    return data


def load_config(explicit: str | None = None) -> dict[str, Any]:
    """Load the selected config without exposing its path or values in output."""

    path, selected_by = selected_config_path(explicit)
    base = {"path": path, "selected_by": selected_by, "data": {}, "status": "missing"}
    if not path.is_file():
        return base
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        base["data"] = _validate(data)
        base["status"] = "ok"
        return base
    except ConfigError as exc:
        base["status"] = "invalid"
        base["reason"] = str(exc)
        return base
    except (OSError, UnicodeError, json.JSONDecodeError):
        base["status"] = "unreadable"
        base["reason"] = "config_could_not_be_read"
        return base


def runtime_path(config: dict[str, Any], name: str) -> str | None:
    entry = (config.get("runtimes") or {}).get(name)
    if isinstance(entry, str):
        return entry
    if isinstance(entry, dict):
        value = entry.get("python_path")
        return value if isinstance(value, str) else None
    return None


def reader_paths(config: dict[str, Any], name: str) -> dict[str, str]:
    value = (config.get("readers") or {}).get(name)
    if not isinstance(value, dict):
        return {}
    return {key: item for key, item in value.items() if isinstance(item, str)}


def configured_names(config_result: dict[str, Any]) -> dict[str, list[str]]:
    data = config_result.get("data") or {}
    return {
        "runtimes": sorted((data.get("runtimes") or {}).keys()),
        "readers": sorted((data.get("readers") or {}).keys()),
    }


def redacted_config_summary(config_result: dict[str, Any]) -> dict[str, Any]:
    """Summarize config state without returning local path values."""

    return {
        "status": config_result.get("status"),
        "selected_by": config_result.get("selected_by"),
        "configured": configured_names(config_result),
        "path_values_emitted": False,
        "reason": config_result.get("reason"),
    }
