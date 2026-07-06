"""Колбэки прогресса сканирования."""

from __future__ import annotations

from typing import Callable, Protocol

ADAPTER_LABELS: dict[str, str] = {
    "habr": "Habr Career",
    "hh_parser": "HeadHunter",
    "hh": "HeadHunter",
    "geekjob": "Geekjob",
    "linkedin": "LinkedIn",
    "habr_rss": "Habr RSS",
    "manual": "Вручную",
}


class ScanProgressFn(Protocol):
    def __call__(self, fraction: float, message: str, source: str | None = None) -> None: ...


def label_for(adapter_name: str) -> str:
    return ADAPTER_LABELS.get(adapter_name, adapter_name)
