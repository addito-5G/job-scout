[Русский 🇷🇺](README_ru.md) / **English 🇺🇸**

# NextMove

**AI Career Copilot** — built to help you **get hired**, not just browse vacancies.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> Personal job-search assistant (Product Manager focus). GitHub repo: [`job-scout`](https://github.com/addito-5G/job-scout). UI brand: **NextMove**. Not SaaS, not mass auto-apply — analysis, prioritization, and application materials with you in the loop.

**Core question:** *what should I do today to maximize my chances of getting an offer?*

---

## Screenshots

### Today — daily briefing

![Today screen: briefing, match score, Apply CTA, daily insights](docs/images/today-briefing.png)

### Vacancy — AI Match & cover letter

![Vacancy detail: AI Match, skills, cover letter](docs/images/vacancy-match-letter.png)

### Market — Market Insights

![Market Insights: demand, salary, match distribution](docs/images/market-insights.png)

---

## Why it exists

| Pain | How NextMove helps |
|------|---------------------|
| Three platforms, three tabs | Auto-scan **hh.ru**, **Habr Career**, **Geekjob** |
| Hundreds of jobs — where to focus | AI Match % + matched / missing skills |
| Role switch (analyst → PM) | Profile filter without wiping the DB |
| Applying takes time | Cover letter draft per vacancy |
| No sense of progress | Application funnel + daily briefing |

---

## Features

| Section | Purpose |
|---------|---------|
| **Today** | Daily briefing: top action, insights, metrics |
| **Opportunities** | Prioritized list with match score and quick actions |
| **Saved / Applications** | Job search CRM funnel |
| **Resume** | AI Resume Coach — what to strengthen for the market |
| **Market** | Market Insights — demand, salary, skills |
| **Career Agent** | Search preferences (role, keywords, salary) |

Pipeline: **scan → enrich → fast/deep match → cover letter**. Optional daily run at 09:00 via macOS launchd.

---

## How it works

```mermaid
flowchart LR
    R[Resume .md] --> P[Candidate profile]
    P --> S[Search settings]
    HH[hh.ru] --> SC[Scan service]
    HB[Habr] --> SC
    GJ[Geekjob] --> SC
    SC --> DB[(SQLite + Alembic)]
    DB --> M[AI Match]
    M --> UI[Streamlit UI]
    M --> CL[Cover letter]
```

### AI Router

| Task | Primary | Fallback |
|------|---------|----------|
| `parse_resume`, `fast_match` | **Ollama** | Yandex → Groq |
| `cover_letter`, `suggest_filters` | **YandexGPT** | Groq → Ollama |
| `match_vacancy_deep`, `improve_resume` | **Groq** | Yandex → Ollama |

Responses are cached in SQLite (`ai_cache`) with usage tracking.

---

## Quick start

### 1. Clone & install

```bash
git clone https://github.com/addito-5G/job-scout.git
cd job-scout

python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

### 2. Configure

```bash
cp .env.example .env
```

Minimum for a useful run:

| Variable | Purpose |
|----------|---------|
| `OLLAMA_MODEL` | Local parsing & fast match ([Ollama](https://ollama.com)) |
| `GROQ_API_KEY` | Deep vacancy analysis |
| `YC_FOLDER_ID`, `YC_KEY_PATH` | YandexGPT cover letters |
| `CONTACT_PHONE`, `CONTACT_TELEGRAM`, `CONTACT_LINKEDIN` | Signature in letters |
| `DATABASE_URL` | SQLite path (default `sqlite:///./data/vacancies.db`) |
| `RESUME_PATH` | Path to your resume `.md` |

Full list: [`.env.example`](.env.example).

### 3. Initialize DB & run UI

```bash
python scripts/init_db.py
streamlit run app.py --server.port 8502
```

Open **http://localhost:8502** → upload resume → **Scan market** in the sidebar.

**macOS shortcut:** double-click `Запустить Job Scout.command`

### 4. First-time setup (CLI)

```bash
python scripts/setup.py      # profile + AI search settings
python scripts/scan.py       # fetch vacancies
python scripts/match.py --limit 50
```

### Optional: browser enrich & schedule

```bash
pip install -r requirements-browser.txt
bash scripts/install_schedule.sh
```

---

## Project structure

```
job-scout/                    # repo name (UI brand: NextMove)
├── app.py                    # Streamlit entry point
├── pyproject.toml            # package metadata & dev deps
├── alembic/                  # DB migrations
├── config/                   # criteria.yaml, sources.yaml, schedule
├── ui/                       # Streamlit pages & design system
├── scripts/                  # CLI tools
├── tests/                    # pytest suite (49 tests)
└── src/
    ├── config.py             # .env loader
    ├── config_loader.py      # YAML config
    ├── cli_logging.py        # shared CLI logging
    ├── domain/               # domain types (e.g. role)
    ├── ai/                   # router, cache, prompts
    ├── db/
    │   ├── tables.py         # SQLAlchemy ORM (source of truth)
    │   ├── engine.py         # connection & init_db()
    │   ├── migrations.py     # Alembic upgrade / legacy stamp
    │   └── repositories/     # data access
    ├── services/             # business logic
    │   ├── scan_service.py
    │   ├── match_service.py
    │   ├── cover_letter_service.py
    │   └── vacancy_service/  # listing, detail, writes
    └── adapters/             # hh, habr, geekjob parsers
```

Install in editable mode (`pip install -e ".[dev]"`) so `scripts/` and `ui/` import `src/` without `sys.path` hacks.

---

## CLI reference

| Command | Description |
|---------|-------------|
| `python scripts/init_db.py` | Create / migrate SQLite schema |
| `python scripts/setup.py` | Full onboarding: profile + search settings |
| `python scripts/scan.py` | Scan configured sources |
| `python scripts/match.py --limit 50` | Run AI matching |
| `python scripts/enrich.py` | Enrich vacancy descriptions |
| `python scripts/review.py list` | Review queue in terminal |
| `python scripts/daily_update.py` | Scheduled pipeline (scan + match + metrics) |

---

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -q
```

### Database migrations (Alembic)

Schema is defined in `src/db/tables.py`. `init_db()` runs `alembic upgrade head` automatically.

```bash
alembic upgrade head    # apply migrations
alembic current         # show revision
alembic history
```

Legacy databases created before Alembic are stamped to `head` after lightweight column fixes.

---

## Human-in-the-loop

NextMove **does not** send applications for you. It prepares prioritization, match analysis, and cover letter drafts — you review and submit on each platform.

Respect platform Terms of Service. Do not use for aggressive scraping.

---

## Author

- GitHub: [@addito-5G](https://github.com/addito-5G)
- Telegram: [@addito](https://t.me/addito)
- Email: [addito1@yandex.ru](mailto:addito1@yandex.ru)

Questions and ideas → [Issues](https://github.com/addito-5G/job-scout/issues)

---

## License

[MIT](LICENSE)
