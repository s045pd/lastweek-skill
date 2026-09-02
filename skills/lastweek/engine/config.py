"""Config from process env and ~/.config/lastweek/env."""

from __future__ import annotations

import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "lastweek"
ENV_PATH = CONFIG_DIR / "env"
DEFAULT_SAVE_DIR = Path.home() / "Documents" / "LastWeek"


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_config() -> dict[str, str]:
    merged = _parse_env_file(ENV_PATH)
    for key, value in os.environ.items():
        if value:
            merged[key] = value
    return merged


def save_dir(config: dict[str, str] | None = None) -> Path:
    values = config or load_config()
    raw = values.get("LASTWEEK_SAVE_DIR") or str(DEFAULT_SAVE_DIR)
    path = Path(raw).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    return path


def github_token(config: dict[str, str] | None = None) -> str | None:
    values = config or load_config()
    token = values.get("GITHUB_TOKEN") or values.get("GH_TOKEN")
    if token:
        return token
    import shutil
    import subprocess

    if not shutil.which("gh"):
        return None
    try:
        completed = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    got = completed.stdout.strip()
    return got or None


def brave_key(config: dict[str, str] | None = None) -> str | None:
    values = config or load_config()
    return values.get("BRAVE_API_KEY") or values.get("LASTWEEK_BRAVE_API_KEY") or None
