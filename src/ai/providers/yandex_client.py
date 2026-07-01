from __future__ import annotations

import json
import time
from pathlib import Path

import jwt
import requests

import config
from ai.providers.base import BaseAIProvider
from ai.schemas.result import AIResult


class YandexGPTClient(BaseAIProvider):
    name = "yandex"

    def __init__(
        self,
        folder_id: str | None = None,
        key_path: str | None = None,
        model: str | None = None,
    ):
        self.folder_id = folder_id or config.YC_FOLDER_ID
        self.key_path = Path(key_path or config.YC_KEY_PATH)
        self.model = model or config.YANDEX_MODEL
        self._iam_token: str | None = None
        self._iam_expires_at: float = 0

    def _get_iam_token(self) -> str:
        if self._iam_token and time.time() < self._iam_expires_at - 60:
            return self._iam_token

        with self.key_path.open(encoding="utf-8") as f:
            key_data = json.load(f)

        now = int(time.time())
        payload = {
            "aud": "https://iam.api.cloud.yandex.net/iam/v1/tokens",
            "iss": key_data["service_account_id"],
            "iat": now,
            "exp": now + 3600,
        }
        encoded = jwt.encode(
            payload,
            key_data["private_key"],
            algorithm="PS256",
            headers={"kid": key_data["id"]},
        )
        response = requests.post(
            "https://iam.api.cloud.yandex.net/iam/v1/tokens",
            json={"jwt": encoded},
            timeout=30,
        )
        response.raise_for_status()
        self._iam_token = response.json()["iamToken"]
        self._iam_expires_at = now + 3600
        return self._iam_token

    def complete(self, task_type: str, prompt: str, *, system: str | None = None) -> AIResult:
        iam_token = self._get_iam_token()
        messages = []
        if system:
            messages.append({"role": "system", "text": system})
        messages.append({"role": "user", "text": prompt})

        body = {
            "modelUri": f"gpt://{self.folder_id}/{self.model}",
            "completionOptions": {
                "stream": False,
                "temperature": 0.3,
                "maxTokens": "4000",
            },
            "messages": messages,
        }
        response = requests.post(
            "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
            headers={
                "Authorization": f"Bearer {iam_token}",
                "Content-Type": "application/json",
            },
            json=body,
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        content = data["result"]["alternatives"][0]["message"]["text"]
        usage = data["result"].get("usage", {})
        input_tokens = int(usage.get("inputTextTokens", 0))
        output_tokens = int(usage.get("completionTokens", 0))
        total_tokens = int(usage.get("totalTokens", input_tokens + output_tokens))

        return AIResult(
            content=content,
            provider=self.name,
            model=self.model,
            task_type=task_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
        )
