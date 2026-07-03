"""Общая настройка логирования для CLI-скриптов."""

from __future__ import annotations

import logging

CLI_LOG_FORMAT = "%(message)s"


def setup_cli_logging(*, level: int = logging.INFO) -> logging.Logger:
    """Единый формат stdout для scan/match/enrich/daily_update."""
    logging.basicConfig(level=level, format=CLI_LOG_FORMAT)
    return logging.getLogger("job_scout.cli")
