from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import ScanRun


def start_scan_run(session: Session, *, profile_id: int | None = None, settings_id: int | None = None) -> int:
    row = ScanRun(
        started_at=datetime.utcnow(),
        profile_id=profile_id,
        search_settings_id=settings_id,
        status="running",
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row.id


def finish_scan_run(
    session: Session,
    run_id: int,
    *,
    total_found: int = 0,
    new_added: int = 0,
    updated: int = 0,
    skipped: int = 0,
    errors: int = 0,
    error_log: str = "",
    status: str = "completed",
    hh_found: int = 0,
    habr_found: int = 0,
    geekjob_found: int = 0,
    # legacy kwargs
    scraped: int | None = None,
    new_count: int | None = None,
    enriched: int = 0,
) -> None:
    row = session.get(ScanRun, run_id)
    if not row:
        return
    row.finished_at = datetime.utcnow()
    if row.started_at and row.finished_at:
        row.duration_seconds = int((row.finished_at - row.started_at).total_seconds())
    row.total_found = scraped if scraped is not None else total_found
    row.new_added = new_count if new_count is not None else new_added
    row.updated = updated
    row.skipped = skipped
    row.errors = errors
    row.error_log = error_log or None
    row.status = status
    row.hh_found = hh_found
    row.habr_found = habr_found
    row.geekjob_found = geekjob_found
    session.commit()


def get_last_scan_run(session: Session) -> ScanRun | None:
    return session.execute(
        select(ScanRun)
        .where(ScanRun.status.in_(("completed", "completed_with_errors")))
        .order_by(ScanRun.finished_at.desc().nullslast(), ScanRun.started_at.desc())
        .limit(1)
    ).scalar_one_or_none()


def is_scan_running(session: Session) -> bool:
    row = session.execute(
        select(ScanRun)
        .where(ScanRun.status == "running")
        .order_by(ScanRun.started_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    if not row:
        return False
    if row.started_at and (datetime.utcnow() - row.started_at).total_seconds() > 7200:
        finish_scan_run(session, row.id, status="failed", error_log="timeout")
        return False
    return True
