from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

import config
from db.models import AIUsageLog
from time_utils import utc_now

logger = logging.getLogger(__name__)


@dataclass
class UsageSnapshot:
    provider: str
    requests_today: int = 0
    tokens_today: int = 0
    request_limit: int | None = None
    token_limit: int | None = None
    request_usage_pct: float = 0.0
    token_usage_pct: float = 0.0
    warnings: list[str] = field(default_factory=list)

    @property
    def near_limit(self) -> bool:
        return bool(self.warnings)


class UsageTracker:
    LIMITS = {
        "ollama": {"requests": None, "tokens": None},
        "yandex": {"requests": None, "tokens": config.YANDEX_DAILY_TOKEN_LIMIT},
        "groq": {"requests": config.GROQ_DAILY_REQUEST_LIMIT, "tokens": None},
    }

    def __init__(self, session: Session):
        self.session = session
        self._warn_threshold = config.USAGE_WARN_THRESHOLD

    def _today_start(self) -> datetime:
        now = utc_now()
        return now.replace(hour=0, minute=0, second=0, microsecond=0)

    def _usage_today(self, provider: str) -> tuple[int, int]:
        since = self._today_start()
        rows = self.session.execute(
            select(
                func.count(AIUsageLog.id),
                func.coalesce(func.sum(AIUsageLog.total_tokens), 0),
            ).where(
                AIUsageLog.provider == provider,
                AIUsageLog.cache_hit.is_(False),
                AIUsageLog.success.is_(True),
                AIUsageLog.created_at >= since,
            )
        ).one()
        return int(rows[0] or 0), int(rows[1] or 0)

    def snapshot(self, provider: str) -> UsageSnapshot:
        limits = self.LIMITS.get(provider, {})
        requests, tokens = self._usage_today(provider)
        req_limit = limits.get("requests")
        tok_limit = limits.get("tokens")

        snap = UsageSnapshot(
            provider=provider,
            requests_today=requests,
            tokens_today=tokens,
            request_limit=req_limit,
            token_limit=tok_limit,
        )

        if req_limit:
            snap.request_usage_pct = requests / req_limit
            if snap.request_usage_pct >= self._warn_threshold:
                msg = (
                    f"⚠️ {provider}: {snap.request_usage_pct:.0%} дневного лимита запросов "
                    f"({requests}/{req_limit})"
                )
                snap.warnings.append(msg)
                logger.warning(msg)

        if tok_limit:
            snap.token_usage_pct = tokens / tok_limit
            if snap.token_usage_pct >= self._warn_threshold:
                msg = (
                    f"⚠️ {provider}: {snap.token_usage_pct:.0%} дневного лимита токенов "
                    f"({tokens}/{tok_limit})"
                )
                snap.warnings.append(msg)
                logger.warning(msg)

        return snap

    def can_use(self, provider: str) -> bool:
        snap = self.snapshot(provider)
        if snap.request_limit and snap.requests_today >= snap.request_limit:
            return False
        if snap.token_limit and snap.tokens_today >= snap.token_limit:
            return False
        return True

    def log(
        self,
        provider: str,
        task_type: str,
        model: str,
        *,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cache_hit: bool = False,
        success: bool = True,
        error_message: str | None = None,
    ) -> UsageSnapshot:
        total = input_tokens + output_tokens
        self.session.add(
            AIUsageLog(
                provider=provider,
                task_type=task_type,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total,
                cache_hit=cache_hit,
                success=success,
                error_message=error_message,
            )
        )
        self.session.commit()
        return self.snapshot(provider)

    def log_cache_hit(self, provider: str, task_type: str) -> None:
        self.session.add(
            AIUsageLog(
                provider=provider,
                task_type=task_type,
                model="cache",
                cache_hit=True,
                success=True,
            )
        )
        self.session.commit()

    def all_snapshots(self) -> list[UsageSnapshot]:
        return [self.snapshot(p) for p in ("ollama", "yandex", "groq")]

    def summary(self) -> dict:
        return {
            s.provider: {
                "requests_today": s.requests_today,
                "tokens_today": s.tokens_today,
                "request_limit": s.request_limit,
                "token_limit": s.token_limit,
                "warnings": s.warnings,
            }
            for s in self.all_snapshots()
        }
