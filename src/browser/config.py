from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import config

DEFAULT_BROWSER_CONFIG = config.ROOT / "browser_config.json"


def load_browser_config(path: str | Path | None = None) -> dict[str, Any]:
    cfg_path = Path(path or config.BROWSER_CONFIG_PATH)
    if not cfg_path.exists():
        return {}
    with cfg_path.open(encoding="utf-8") as f:
        return json.load(f)
