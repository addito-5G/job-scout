# Role: data agent

You own persistence, normalization, listing filters, and deduplication.

## Goals
- Stable schema via Alembic
- Idempotent upserts (source + external_id)
- Fast list/detail queries for UI

## Touch
- `src/db/`, `alembic/`
- `src/services/vacancy_*`, match repos
- migrations only with upgrade path

## Do not
- Change scrape URL params without parser agent
- Embed AI prompts in SQL layers
