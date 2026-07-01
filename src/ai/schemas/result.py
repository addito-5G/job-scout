from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AIResult:
    content: str
    provider: str
    model: str
    task_type: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cache_hit: bool = False
    parsed: dict[str, Any] | None = None
    warnings: list[str] = field(default_factory=list)

    def to_cache_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "provider": self.provider,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "parsed": self.parsed,
        }

    @classmethod
    def from_cache_dict(cls, task_type: str, data: dict[str, Any]) -> "AIResult":
        return cls(
            content=data.get("content", ""),
            provider=data.get("provider", ""),
            model=data.get("model", ""),
            task_type=task_type,
            input_tokens=data.get("input_tokens", 0),
            output_tokens=data.get("output_tokens", 0),
            total_tokens=data.get("total_tokens", 0),
            cache_hit=True,
            parsed=data.get("parsed"),
        )
