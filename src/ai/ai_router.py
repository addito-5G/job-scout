from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

from sqlalchemy.orm import Session

import config
from ai.cache import AICacheStore
from ai.providers import GroqClient, OllamaClient, YandexGPTClient
from ai.providers.base import BaseAIProvider
from ai.routing import FALLBACK_CHAIN, TASK_ROUTING
from ai.schemas.result import AIResult
from ai.task_prompts import build_task_prompt
from ai.usage_tracker import UsageTracker

logger = logging.getLogger(__name__)


class AIRouterError(Exception):
    pass


class AIRouter:
    def __init__(self, session: Session):
        self.session = session
        self.cache = AICacheStore(session)
        self.usage = UsageTracker(session)
        self._providers: dict[str, BaseAIProvider] = {
            "ollama": OllamaClient(),
            "yandex": YandexGPTClient(),
            "groq": GroqClient(),
        }

    def _provider_chain(self, task_type: str, force_provider: str | None = None) -> list[str]:
        primary = force_provider or TASK_ROUTING.get(task_type, "ollama")
        chain = [primary]
        for fb in FALLBACK_CHAIN.get(primary, []):
            if fb not in chain:
                chain.append(fb)
        return chain

    def _build_prompt(self, task_type: str, payload: dict[str, Any]) -> tuple[str, str | None]:
        try:
            return build_task_prompt(task_type, payload)
        except ValueError as exc:
            raise AIRouterError(str(exc)) from exc

    @staticmethod
    def _extract_json(content: str) -> dict[str, Any] | None:
        content = content.strip()
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    return None
        return None

    def _execute_with_retry(
        self,
        provider_name: str,
        task_type: str,
        prompt: str,
        system: str | None,
    ) -> AIResult:
        provider = self._providers[provider_name]
        last_error: Exception | None = None
        max_attempts = config.AI_RETRY_MAX_ATTEMPTS

        for attempt in range(1, max_attempts + 1):
            try:
                result = provider.complete(task_type, prompt, system=system)
                self.usage.log(
                    provider_name,
                    task_type,
                    result.model,
                    input_tokens=result.input_tokens,
                    output_tokens=result.output_tokens,
                    success=True,
                )
                snap = self.usage.snapshot(provider_name)
                result.warnings.extend(snap.warnings)
                return result
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "%s attempt %s/%s failed for %s: %s",
                    provider_name,
                    attempt,
                    max_attempts,
                    task_type,
                    exc,
                )
                if attempt < max_attempts:
                    delay = config.AI_RETRY_BASE_DELAY * (2 ** (attempt - 1))
                    time.sleep(delay)

        self.usage.log(
            provider_name,
            task_type,
            getattr(provider, "model", provider_name),
            success=False,
            error_message=str(last_error),
        )
        raise AIRouterError(f"{provider_name} failed after {max_attempts} attempts: {last_error}")

    def route(
        self,
        task_type: str,
        payload: dict[str, Any],
        *,
        force_provider: str | None = None,
        use_cache: bool = True,
        parse_json: bool = False,
    ) -> AIResult:
        cache_key = self.cache.make_key(task_type, payload)

        if use_cache:
            cached = self.cache.get(cache_key)
            if cached:
                cached.task_type = task_type
                self.usage.log_cache_hit(cached.provider or "cache", task_type)
                return cached

        prompt, system = self._build_prompt(task_type, payload)
        errors: list[str] = []

        for provider_name in self._provider_chain(task_type, force_provider):
            if not self.usage.can_use(provider_name):
                msg = f"Лимит {provider_name} исчерпан, пробуем следующий провайдер"
                logger.warning(msg)
                errors.append(msg)
                continue

            try:
                result = self._execute_with_retry(provider_name, task_type, prompt, system)
                if parse_json:
                    result.parsed = self._extract_json(result.content)
                if use_cache:
                    self.cache.set(cache_key, task_type, result)
                return result
            except AIRouterError as exc:
                errors.append(str(exc))
                logger.warning("Fallback from %s: %s", provider_name, exc)

        raise AIRouterError(
            f"Все провайдеры недоступны для {task_type}: " + "; ".join(errors)
        )

    def clear_cache(self, **kwargs) -> int:
        return self.cache.clear(**kwargs)

    def usage_summary(self) -> dict:
        return self.usage.summary()

    def register_provider(self, name: str, provider: BaseAIProvider) -> None:
        self._providers[name] = provider
