# NextMove multi-agent architecture

This folder defines **roles and prompts** for Cursor agents and (optionally) in-app pipelines.
It does **not** replace production services in `src/` — parsers, scan, match, and Streamlit UI stay the source of truth.

## Layers

```text
┌─────────────────────────────────────────────────────────┐
│  Cursor IDE agents (rules + MCP + graphify)             │
│  roles: parser · data · ai · ui · ops                   │
└───────────────────────────┬─────────────────────────────┘
                            │ edits / debug
┌───────────────────────────▼─────────────────────────────┐
│  App services (src/)                                    │
│  scan → upsert/dedupe → match/fit → UI                  │
│  AI routing: ollama / yandex / groq (src/ai/routing.py) │
└─────────────────────────────────────────────────────────┘
```

## Roles (one agent = one zone)

| Role | Owns | Do not touch |
|------|------|--------------|
| `parser` | `src/adapters/`, `src/parsers/`, `config/sources.yaml` | UI layout, AI prompts |
| `data` | repos, migrations, dedupe/normalize, listing filters | browser scraping hacks |
| `ai` | `src/ai/`, task prompts, routing, fit/cover letter | HH HTML fetch details |
| `ui` | `ui/`, Streamlit UX | DB schema without migration |
| `ops` | scan schedule, MCP config, local Ollama wiring | product copy experiments |

## LLM split (practical)

| Work | Prefer |
|------|--------|
| Code edits in Cursor | Cursor cloud model **or** Ollama code model via custom endpoint |
| Resume parse / categorize / filters | Ollama (`TASK_ROUTING`) |
| Cover letter / improve resume / company brief | YandexGPT |
| Fit advice | Grok/Groq (as configured) |
| Experimental page → structured JSON | Crawl4AI + Ollama (offline experiments only) |

## Related Cursor files

- Rules: `.cursor/rules/`
- MCP example: `.cursor/mcp.json.example`
- Code graph: `graphify-out/` + `.cursor/rules/graphify.mdc`

## What not to adopt as core

- Open WebUI / Dify as the product UI (chat platforms, not NextMove)
- Firecrawl as the primary HH scanner (you already have InitialState parsing)
- CrewAI as the IDE layer (use for optional app prototypes only)
