from __future__ import annotations

from abc import ABC, abstractmethod

from ai.schemas.result import AIResult


class BaseAIProvider(ABC):
    name: str

    @abstractmethod
    def complete(self, task_type: str, prompt: str, *, system: str | None = None) -> AIResult:
        ...
