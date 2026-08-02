# Role: ai agent

You own LLM tasks and provider routing.

## Goals
- Task → provider mapping stays explicit in `src/ai/routing.py`
- Prompts live under `src/ai/prompts/`
- Prefer Ollama for cheap local tasks; Yandex/Grok for quality-critical text

## Touch
- `src/ai/`
- `src/services/*_service.py` that call AI
- `tests/test_task_prompts.py` and related

## Do not
- Call external LLMs from adapters/parsers
- Store API keys in code
