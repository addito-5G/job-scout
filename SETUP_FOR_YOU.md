# Что сделать тебе (остальное уже сделано)

Я настроил агент-слой в репозитории сам. Тебе нужны только клики в Cursor — без этого MCP/модели не подхватятся.

## Сделай 3 шага (5 минут)

### 1. Перезапусти Cursor
Полностью Quit Cursor → открой снова этот проект (`job-scout`).  
Нужно, чтобы подтянулся `.cursor/mcp.json` (Playwright).

### 2. Проверь MCP
`Cursor Settings` → `Tools & MCP` (или Features → MCP):

- должен появиться **playwright** (зелёный);
- если просит Approve / Enable — нажми **Enable**.

GitHub MCP у тебя уже есть глобально — его трогать не нужно.

### 3. (Опционально) Подключи Ollama в Cursor
Если хочешь локальную code-модель в Agent/Chat:

1. `Cursor Settings` → `Models`
2. Add custom / OpenAI-compatible endpoint:
   - Base URL: `http://127.0.0.1:11434/v1`
   - API key: любое слово, например `ollama`
3. Выбери модель: `qwen2.5-coder:7b` (код) или `qwen2.5:14b` (общие задачи)

У тебя Ollama уже установлена и модели уже скачаны — только указать endpoint в UI.

---

## Как пользоваться дальше (без лишней возни)

В чате пиши роль одной строкой, например:

- `Действуй как parser agent` — парсинг HH
- `Действуй как ai agent` — промпты / routing
- `Действуй как ui agent` — Streamlit

Или **критик** (это то, что реально спорит с решениями):

- `поспорь с этим` / `@challenge`
- `@challenge plan` · `@challenge mid` · `@challenge commit` · `@challenge pr`

Файлы: `agents/prompts/`, `agents/CHALLENGE_PROMPTS.md`, skill `.cursor/skills/devils-advocate/`.

Production-скан по-прежнему: Streamlit → Scan (не Crawl4AI).

---

## Если что-то красное

| Симптом | Что сделать |
|---------|-------------|
| playwright не зелёный | Quit Cursor ещё раз; проверь, что установлен Node.js (`node -v`) |
| Ollama model error | Открой приложение Ollama; `ollama list` в терминале |
| Скан «ничего не найдено» | Скажи мне — это баг парсера, чиню я |

Больше от тебя ничего не нужно, пока не упрёмся в Approve/ключ в UI.
