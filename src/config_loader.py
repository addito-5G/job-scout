"""Единая загрузка YAML-конфигов из config/."""

from __future__ import annotations

from pathlib import Path

import yaml

import config

CONFIG_DIR = config.ROOT / "config"
CRITERIA_PATH = CONFIG_DIR / "criteria.yaml"
SOURCES_PATH = CONFIG_DIR / "sources.yaml"
SCHEDULE_PATH = CONFIG_DIR / "schedule.yaml"


def load_yaml(path: Path) -> dict:
    """Прочитать YAML-файл; пустой файл → {}."""
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_criteria() -> dict:
    return load_yaml(CRITERIA_PATH)


def load_sources() -> dict:
    return load_yaml(SOURCES_PATH)


def load_criteria_with_browser() -> dict:
    """criteria.yaml + секция browser из sources.yaml (как в daily_update / enrich)."""
    criteria = load_criteria()
    criteria["browser"] = load_sources().get("browser", {})
    return criteria
