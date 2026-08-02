# NextMove blind spots (adversarial checklist)

Domain traps for vacancy scanning + AI career copilot.

## Scraping / HH

- HTML entity-escaped `HH-Lux-InitialState` (`&#34;`) → must `html.unescape` before JSON
- Empty scan in ~seconds usually means parse/HTTP failure, not "no jobs" — check `adapter.errors` / UI
- Missing `published_at` after enrich: **kept** when HH request already used `search_period` (logged as `kept_undated`); dated rows older than window are skipped (`skipped_old`)
- Filter runs only after optional detail enrich so card dates can fill in
- Missing `search_period` on cached queries is normalized to 7 on read
- Rate limits / bot pages: captcha-form / «доступ ограничен» without InitialState
- Detail enrich (`use_for_scan`) multiplies latency and ban risk
- Replacing production parser with Firecrawl/Crawl4AI loses domain structure

## Data / dedupe

- Identity is `(source, external_id)` — fragile if HH id missing
- Upsert must not wipe enriched fields with empty scrape stubs
- `published_at` timezone-naive vs aware comparisons
- Listing filters in UI vs DB must stay consistent

## Architecture layers

- `ui/` must not run raw SQL — use services/facades
- Adapters must not call Yandex/Grok directly — go through `src/ai/`
- Migrations without rollback story for SQLite/prod

## AI routing

- Task→provider map lives in `src/ai/routing.py` — hardcoding a vendor elsewhere drifts
- Local Ollama quality ≠ cloud; fit/cover letter quality regressions
- Prompt changes without cache TTL awareness → stale advice

## Product / UX

- Scan progress that lies ("done" with 0 found and swallowed errors)
- Fit score / advice presented as truth without confidence caveats

## Security

- Tokens in `.cursor/mcp.json` / `.env` never committed
- Scraped HTML must not be executed; sanitize if rendered
- Manual URL ingest as SSRF if fetcher is too trusting

## Questions that catch AI optimism

1. What happens when HH returns 200 with a challenge page?
2. What if `published_at` is null — do we drop or keep?
3. If enrich fails mid-scan, is partial state safe to show?
4. Is this the simplest fix, or a new framework?
5. Which layer owns this — parser, data, ai, or ui?
