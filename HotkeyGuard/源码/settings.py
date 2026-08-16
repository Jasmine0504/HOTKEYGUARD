# -*- coding: utf-8 -*-
"""设置持久化：%APPDATA%/HotkeyGuard/settings.json"""

import json
import os
from pathlib import Path

from rules import RULES, DEFAULT_BLOCKED

APP_NAME = "HotkeyGuard"


def config_dir() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home())
    d = Path(base) / APP_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


def config_path() -> Path:
    return config_dir() / "settings.json"


def load() -> dict:
    cfg = {"mode": "normal", "blocked": list(DEFAULT_BLOCKED), "topmost": False}
    try:
        p = config_path()
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            if data.get("mode") in ("normal", "game"):
                cfg["mode"] = data["mode"]
            cfg["blocked"] = [b for b in data.get("blocked", []) if b in RULES]
            cfg["topmost"] = bool(data.get("topmost", False))
    except Exception:
        pass
    return cfg


def save(cfg: dict) -> None:
    try:
        config_path().write_text(
            json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception:
        pass
