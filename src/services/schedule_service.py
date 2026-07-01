from __future__ import annotations

from datetime import datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

import config

DEFAULT_SCHEDULE: dict = {
    "enabled": True,
    "scan_time": "09:00",
    "timezone": "Europe/Moscow",
    "match_limit": 50,
}

SCHEDULE_PATH = config.ROOT / "config" / "schedule.yaml"


def _parse_time(value: str) -> time:
    hour, minute = value.strip().split(":", 1)
    return time(hour=int(hour), minute=int(minute))


def load_schedule() -> dict:
    if not SCHEDULE_PATH.exists():
        save_schedule(DEFAULT_SCHEDULE)
        return DEFAULT_SCHEDULE.copy()
    with SCHEDULE_PATH.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    merged = {**DEFAULT_SCHEDULE, **data}
    return merged


def save_schedule(data: dict) -> dict:
    merged = {**DEFAULT_SCHEDULE, **data}
    SCHEDULE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SCHEDULE_PATH.open("w", encoding="utf-8") as f:
        yaml.safe_dump(merged, f, allow_unicode=True, sort_keys=False)
    return merged


def schedule_timezone() -> ZoneInfo:
    tz_name = load_schedule().get("timezone", "Europe/Moscow")
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return ZoneInfo("Europe/Moscow")


def format_dt_msk(dt: datetime | None) -> str:
    if dt is None:
        return "—"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    local = dt.astimezone(schedule_timezone())
    return local.strftime("%d.%m.%Y %H:%M")


def next_scan_datetime(*, now: datetime | None = None) -> datetime | None:
    schedule = load_schedule()
    if not schedule.get("enabled", True):
        return None
    tz = schedule_timezone()
    now = (now or datetime.now(tz)).astimezone(tz)
    scan_t = _parse_time(str(schedule.get("scan_time", "09:00")))
    candidate = now.replace(
        hour=scan_t.hour,
        minute=scan_t.minute,
        second=0,
        microsecond=0,
    )
    if candidate <= now:
        candidate += timedelta(days=1)
    return candidate


def next_scan_label() -> str:
    schedule = load_schedule()
    if not schedule.get("enabled", True):
        return "автообновление выключено"
    nxt = next_scan_datetime()
    if not nxt:
        return "—"
    return nxt.strftime("%d.%m в %H:%M")
