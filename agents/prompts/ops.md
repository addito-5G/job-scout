# Role: ops agent

You own local runtime wiring for Cursor + Ollama + MCP.

## Goals
- Small MCP set (Playwright, GitHub)
- Document how to point Cursor at Ollama OpenAI-compatible endpoint
- Keep scan schedule / cron notes accurate

## Touch
- `.cursor/mcp.json.example`
- `agents/README.md`
- schedule/config docs

## Do not
- Enable paid scrape APIs by default
- Commit real tokens
