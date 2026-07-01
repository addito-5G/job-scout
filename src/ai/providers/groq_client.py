from __future__ import annotations

from groq import Groq

import config
from ai.providers.base import BaseAIProvider
from ai.schemas.result import AIResult


class GroqClient(BaseAIProvider):
    name = "groq"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ):
        self.model = model or config.GROQ_MODEL
        self._client = Groq(api_key=api_key or config.GROQ_API_KEY)

    def complete(self, task_type: str, prompt: str, *, system: str | None = None) -> AIResult:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        completion = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
            max_tokens=4000,
        )
        content = completion.choices[0].message.content or ""
        usage = completion.usage
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0
        total_tokens = usage.total_tokens if usage else input_tokens + output_tokens

        return AIResult(
            content=content,
            provider=self.name,
            model=self.model,
            task_type=task_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
        )
