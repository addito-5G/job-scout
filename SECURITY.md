# Security

## Do not commit

- `.env` — API keys (Groq, Yandex, HH OAuth)
- `yandex_key.json` — Yandex Cloud service account
- `data/vacancies.db` — scraped vacancies and match history
- `data/resumes/` — personal resume files
- `browser_config.json` — may contain local machine paths

All of the above are listed in `.gitignore`.

## Before pushing

```bash
git status
git diff --cached
# ensure no secrets in staged files
rg -i "gsk_|sk-|api_key|password|BEGIN PRIVATE" --glob '!venv/**' --glob '!.git/**'
```

## Responsible use

Job Scout is a personal pet project. Respect the terms of service of job boards (hh.ru, Habr Career, Geekjob). Use reasonable request rates; the project is not intended for commercial scraping at scale.
