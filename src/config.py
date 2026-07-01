"""Загрузка настроек из .env."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

# Ollama
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:14b")

# Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_DAILY_REQUEST_LIMIT = int(os.getenv("GROQ_DAILY_REQUEST_LIMIT", "14000"))

# YandexGPT
YC_FOLDER_ID = os.getenv("YC_FOLDER_ID", "")
YC_KEY_PATH = os.getenv("YC_KEY_PATH", str(ROOT / "yandex_key.json"))
YANDEX_MODEL = os.getenv("YANDEX_MODEL", "yandexgpt/latest")
YANDEX_DAILY_TOKEN_LIMIT = int(os.getenv("YANDEX_DAILY_TOKEN_LIMIT", "50000"))

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/vacancies.db")

# Browser
BROWSER_CONFIG_PATH = os.getenv("BROWSER_CONFIG_PATH", str(ROOT / "browser_config.json"))

# AI router
AI_CACHE_TTL_DAYS = int(os.getenv("AI_CACHE_TTL_DAYS", "30"))
AI_RETRY_MAX_ATTEMPTS = int(os.getenv("AI_RETRY_MAX_ATTEMPTS", "3"))
AI_RETRY_BASE_DELAY = float(os.getenv("AI_RETRY_BASE_DELAY", "1.0"))
USAGE_WARN_THRESHOLD = float(os.getenv("USAGE_WARN_THRESHOLD", "0.8"))

# Resume test path (Obsidian)
DEFAULT_RESUME_PATH = os.path.expanduser(
    os.getenv("RESUME_PATH", "~/Documents/resume.md")
)
