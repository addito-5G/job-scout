"""UTC timestamps compatible with naive SQLite DateTime columns."""

from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Naive UTC «сейчас» (как прежний datetime.utcnow())."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
