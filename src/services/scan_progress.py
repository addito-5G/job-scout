"""Колбэки прогресса сканирования."""

from __future__ import annotations

from typing import Protocol

ADAPTER_LABELS: dict[str, str] = {
    "hh_parser": "HeadHunter",
    "hh": "HeadHunter",
    "manual": "Вручную",
}


class ScanProgressFn(Protocol):
    def __call__(self, fraction: float, message: str, source: str | None = None) -> None: ...


def label_for(adapter_name: str) -> str:
    return ADAPTER_LABELS.get(adapter_name, adapter_name)
