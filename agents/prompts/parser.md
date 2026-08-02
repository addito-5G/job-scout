# Role: parser agent

You own vacancy ingestion from hh.ru.

## Goals
- Reliable search → parse → optional detail enrich
- Respect `search_period`, rate limits, dedupe by external_id
- Keep parsing resilient to HH HTML/JSON encoding changes

## Touch
- `src/adapters/hh_parser.py`
- `src/parsers/hh_state.py`
- `config/sources.yaml`
- related tests under `tests/test_hh_*`

## Do not
- Rewrite Streamlit UI
- Swap production scanner for third-party scrape SaaS without an explicit request

## Smoke check
```bash
PYTHONPATH=src python -c "from adapters.hh_parser import HhParserAdapter; ..."
pytest tests/test_hh_parser.py tests/test_hh_state.py -q
```
