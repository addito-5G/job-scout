from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

import config
from ai.routing import CACHE_TTL_DAYS
from ai.schemas.result import AIResult
from db.models import AICache

logger = logging.getLogger(__name__)


class AICacheStore:
    def __init__(self, session: Session):
        self.session = session

    @staticmethod
    def make_key(task_type: str, payload: dict) -> str:
        raw = json.dumps({"task": task_type, "payload": payload}, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _ttl_days(self, task_type: str) -> int:
        return CACHE_TTL_DAYS.get(task_type, CACHE_TTL_DAYS["default"])

    def get(self, cache_key: str) -> AIResult | None:
        now = datetime.utcnow()
        row = self.session.execute(
            select(AICache).where(AICache.cache_key == cache_key)
        ).scalar_one_or_none()

        if not row:
            return None

        if row.expires_at and row.expires_at < now:
            self.session.delete(row)
            self.session.commit()
            return None

        try:
            data = json.loads(row.response)
        except json.JSONDecodeError:
            return None

        result = AIResult.from_cache_dict(row.task_type, data)
        result.provider = row.provider
        logger.debug("AI cache hit: %s", cache_key[:12])
        return result

    def set(self, cache_key: str, task_type: str, result: AIResult) -> None:
        ttl = self._ttl_days(task_type)
        expires_at = datetime.utcnow() + timedelta(days=ttl)
        payload = json.dumps(result.to_cache_dict(), ensure_ascii=False)

        row = self.session.execute(
            select(AICache).where(AICache.cache_key == cache_key)
        ).scalar_one_or_none()

        if row:
            row.provider = result.provider
            row.task_type = task_type
            row.response = payload
            row.tokens_used = result.total_tokens
            row.expires_at = expires_at
            row.created_at = datetime.utcnow()
        else:
            self.session.add(
                AICache(
                    cache_key=cache_key,
                    provider=result.provider,
                    task_type=task_type,
                    response=payload,
                    tokens_used=result.total_tokens,
                    expires_at=expires_at,
                )
            )
        self.session.commit()

    def clear(
        self,
        *,
        task_type: str | None = None,
        provider: str | None = None,
        expired_only: bool = False,
    ) -> int:
        """Принудительная очистка кэша. Возвращает число удалённых записей."""
        now = datetime.utcnow()
        stmt = delete(AICache)

        if task_type:
            stmt = stmt.where(AICache.task_type == task_type)
        if provider:
            stmt = stmt.where(AICache.provider == provider)
        if expired_only:
            stmt = stmt.where(AICache.expires_at < now)

        result = self.session.execute(stmt)
        self.session.commit()
        deleted = result.rowcount or 0
        logger.info(
            "AI cache cleared: %s entries (task=%s, provider=%s, expired_only=%s)",
            deleted,
            task_type,
            provider,
            expired_only,
        )
        return deleted

    def stats(self) -> dict:
        total = self.session.execute(select(func.count(AICache.id))).scalar() or 0
        now = datetime.utcnow()
        expired = self.session.execute(
            select(func.count(AICache.id)).where(AICache.expires_at < now)
        ).scalar() or 0
        return {"total": total, "expired": expired, "active": total - expired}
