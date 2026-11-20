"""Helpers to read configuration from environment variables (see .env.example).

The settings read the environment only through these, so a value that cannot be parsed
stops the start with a clear message instead of silently falling back to a default.
An empty variable counts as not set (compose passes `NAME=` from .env as empty).
"""

import os
from datetime import time

from django.core.exceptions import ImproperlyConfigured

TRUE = {"1", "true", "yes", "on"}
FALSE = {"0", "false", "no", "off"}


def env_str(name: str, default: str = "") -> str:
    return os.environ.get(name, "").strip() or default


def env_bool(name: str, default: bool = False) -> bool:
    raw = env_str(name).lower()
    if not raw:
        return default
    if raw in TRUE:
        return True
    if raw in FALSE:
        return False
    raise ImproperlyConfigured(f"{name} must be true or false, not {raw!r}.")


def env_int(name: str, default: int) -> int:
    raw = env_str(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        raise ImproperlyConfigured(f"{name} must be a whole number, not {raw!r}.") from None


def env_time(name: str, default: str) -> time:
    raw = env_str(name, default)
    try:
        return time.fromisoformat(raw)
    except ValueError:
        raise ImproperlyConfigured(f"{name} must be a time as HH:MM, not {raw!r}.") from None


def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in env_str(name, default).split(",") if item.strip()]
