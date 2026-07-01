from __future__ import annotations

import ollama

import config
from ai.providers.base import BaseAIProvider
from ai.schemas.result import AIResult


class OllamaClient(BaseAIProvider):
    name = "ollama"

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
    ):
        self.base_url = base_url or config.OLLAMA_BASE_URL
        self.model = model or config.OLLAMA_MODEL
        self._client = ollama.Client(host=self.base_url)

    def complete(self, task_type: str, prompt: str, *, system: str | None = None) -> AIResult:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self._client.chat(model=self.model, messages=messages)
        content = response["message"]["content"]
        input_tokens = response.get("prompt_eval_count") or 0
        output_tokens = response.get("eval_count") or 0

        return AIResult(
            content=content,
            provider=self.name,
            model=self.model,
            task_type=task_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
        )
