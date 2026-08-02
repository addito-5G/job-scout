# Graph Report - job-scout  (2026-08-02)

## Corpus Check
- 176 files · ~61,181 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1181 nodes · 3059 edges · 66 communities (58 shown, 8 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 217 edges (avg confidence: 0.75)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `3195c5c8`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- db/models.py
- select
- vacancy_repo.py
- search_service.py
- resume_advice_service.py
- NextMove
- AIRouter
- linkedin_jobs.py
- task_prompts.py
- render_detail
- fit_score.py
- linkedin_outreach_service.py
- data.py
- fetcher.py
- habr_parser.py
- Vacancy
- hh_state.py
- app.py
- CandidateProfile
- parse_setup_page.py
- build_nakimov_harvard_cv_ru.py
- vacancy_fit_advice_service.py
- profile_service.py
- navigation.py
- cover_letter_service.py
- geekjob_parser.py
- Config
- init_db
- build_nakimov_harvard_cv.py
- PageFetcher
- apply_migrations
- cached_profile_id
- config_loader.py
- schedule_service.py
- scan_service.py
- scheduled_job.py
- review.py
- build_pdf
- list_for_matching
- test_match_service.py
- HhParserAdapter
- match_service.py
- Ежедневный персональный радар вакансий
- test_scheduled_job.py
- BaseModel
- Security
- send_telegram_radar.py
- test_review_cli.py
- test_linkedin_outreach_service.py
- install_schedule.sh
- setup_github_auth.sh
- improve_resume.py
- vacancy_fit_advice.py
- src/config.py
- domain/__init__.py
- job-scout

## God Nodes (most connected - your core abstractions)
1. `CandidateProfile` - 58 edges
2. `AIRouter` - 30 edges
3. `AIResult` - 29 edges
4. `utc_now()` - 29 edges
5. `init_db()` - 27 edges
6. `get_session()` - 25 edges
7. `upsert_vacancy()` - 24 edges
8. `session_scope()` - 23 edges
9. `Vacancy` - 22 edges
10. `loads_json()` - 22 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `snapshot_for_today()`  [INFERRED]
  scripts/daily_update.py → src/analytics.py
- `_bootstrap()` --calls--> `session_scope()`  [INFERRED]
  app.py → src/db/session_scope.py
- `_bootstrap()` --calls--> `get_active_profile()`  [INFERRED]
  app.py → src/services/profile_service.py
- `_bootstrap()` --calls--> `get_active_search_settings()`  [INFERRED]
  app.py → src/services/search_service.py
- `main()` --calls--> `build_analytics()`  [INFERRED]
  scripts/daily_update.py → src/analytics.py

## Import Cycles
- 3-file cycle: `src/services/vacancy_queries.py -> src/services/vacancy_service/__init__.py -> src/services/vacancy_service/company_listing.py -> src/services/vacancy_queries.py`
- 3-file cycle: `src/services/vacancy_queries.py -> src/services/vacancy_service/__init__.py -> src/services/vacancy_service/listing.py -> src/services/vacancy_queries.py`

## Communities (66 total, 8 thin omitted)

### Community 0 - "db/models.py"
Cohesion: 0.06
Nodes (50): DeclarativeBase, AICacheStore, Session, Принудительная очистка кэша. Возвращает число удалённых записей., datetime, Session, UsageSnapshot, UsageTracker (+42 more)

### Community 1 - "select"
Cohesion: 0.06
Nodes (64): get_vacancy_by_id(), get_vacancy_tags(), ensure_company_brief(), Session, Краткая AI-справка о компании-работодателе., build_count_by_source_query(), build_list_vacancies_base(), build_review_list_query() (+56 more)

### Community 2 - "vacancy_repo.py"
Cohesion: 0.06
Nodes (61): _database_url(), Alembic environment: metadata from ORM, URL from config., run_migrations_offline(), run_migrations_online(), backup_db(), _columns(), drop_legacy_tables(), _fetch_all() (+53 more)

### Community 3 - "search_service.py"
Cohesion: 0.06
Nodes (61): SearchSettings, infer_role_from_title(), Единые константы и эвристики роли (PM / аналитик / general). Два пути инференса…, Стабильный ключ роли из названия должности., Роль из названия должности; для неизвестных — slug из title., role_label(), slug_role(), _loads() (+53 more)

### Community 4 - "resume_advice_service.py"
Cohesion: 0.08
Nodes (47): experience_label(), work_format_label(), experience_distribution(), get_metrics(), match_score_buckets(), Session, Vacancy, _salary_mid() (+39 more)

### Community 5 - "NextMove"
Cohesion: 0.04
Nodes (44): 1. Clone & install, 2. Configure, 3. Initialize DB & run UI, 4. First-time setup (CLI), AI: free by design, Author, CLI reference, Database migrations (Alembic) (+36 more)

### Community 6 - "AIRouter"
Cohesion: 0.11
Nodes (12): AIRouter, Any, Session, BaseAIProvider, ABC, GroqClient, OllamaClient, YandexGPTClient (+4 more)

### Community 7 - "linkedin_jobs.py"
Cohesion: 0.10
Nodes (28): LinkedinJobUrlAdapter, LinkedinParserAdapter, Vacancy, Импорт одной вакансии по публичному URL (без авторизации)., Публичный guest API LinkedIn Jobs — без логина и cookies пользователя., build_search_url(), canonical_job_url(), _description_from_jsonld() (+20 more)

### Community 8 - "task_prompts.py"
Cohesion: 0.09
Nodes (24): apply_channel_guidance(), format_cover_letter_prompt(), Правило вступления: не дублировать площадку при отклике там же., Подстановка без str.format — JSON в профиле не ломает шаблон., format_linkedin_outreach_prompt(), _build_analyze_resume_ru(), _build_company_brief(), _build_cover_letter() (+16 more)

### Community 9 - "render_detail"
Cohesion: 0.13
Nodes (28): best_match(), Изменение user_status вакансии (application service для UI и скриптов)., Обновить статус вакансии и закоммитить в БД., set_vacancy_status(), Тесты UI-констант (Фаза 3)., test_recommendation_label_full(), test_recommendation_label_short(), test_recommendation_label_unknown_passthrough() (+20 more)

### Community 10 - "fit_score.py"
Cohesion: 0.14
Nodes (30): _build_gaps(), _build_risks(), _build_strengths(), _build_summary(), compute_fit(), _domain_fit_score(), _experience_fit_score(), _extract_requirements() (+22 more)

### Community 11 - "linkedin_outreach_service.py"
Cohesion: 0.14
Nodes (25): first_name_from(), _is_analyst_tool(), _is_pm_relevant(), match_context_for_cover_letter(), profile_for_cover_letter_json(), profile_for_outreach_json(), Контекст профиля для LinkedIn outreach — факты + углы позиционирования., role_title_for_letter() (+17 more)

### Community 12 - "data.py"
Cohesion: 0.18
Nodes (25): cache_data, Session, Открыть сессию и гарантированно закрыть её. Не делает auto-commit: вызывающий…, session_scope(), cached_company_detail(), cached_company_list(), cached_dashboard_metrics(), cached_experience_chart() (+17 more)

### Community 13 - "fetcher.py"
Cohesion: 0.14
Nodes (12): FetchReport, main(), _probe(), load_browser_config(), Any, Path, CamoufoxFetcher, create_fetcher() (+4 more)

### Community 14 - "habr_parser.py"
Cohesion: 0.13
Nodes (18): HabrParserAdapter, Vacancy, _parse_habr_date(), parse_search_page(), parse_vacancy_json_ld(), parse_vacancy_page(), datetime, Fallback: некоторые страницы содержат JSON-LD. (+10 more)

### Community 15 - "Vacancy"
Cohesion: 0.14
Nodes (10): setter, BaseAdapter, HabrRssAdapter, ManualUrlAdapter, ABC, Vacancy, build_adapters(), DTO для парсеров вакансий. (+2 more)

### Community 16 - "hh_state.py"
Cohesion: 0.19
Nodes (20): find_vacancy_list(), find_vacancy_view(), format_salary(), _join_labels(), _label_from_dict(), parse_compensation(), parse_published(), parse_search_item() (+12 more)

### Community 17 - "app.py"
Cohesion: 0.14
Nodes (15): _bootstrap(), _force_public_stub(), main(), Product identity — AI Career Copilot positioning., inject_design_system(), Design tokens and global styles — Linear / Notion inspired., Стартовый экран: загрузка или вставка резюме., Прочитать резюме из session_state (файл или текст). (+7 more)

### Community 18 - "CandidateProfile"
Cohesion: 0.18
Nodes (21): CandidateProfile, normalize_cover_letter(), _normalize_letter(), Лёгкая постобработка: клише и форматирование. Имя — на стороне AI из резюме., Публичная обёртка над post-processing письма (v8, без изменения логики)., generate_fit_advice(), generate_letter(), generate_outreach() (+13 more)

### Community 19 - "parse_setup_page.py"
Cohesion: 0.19
Nodes (18): estimate_parse_seconds(), Оценка длительности парсинга., Прогресс извлечения ключей из резюме., run_extract_with_progress(), _add_item(), apply_draft_to_lists(), _chip_html(), inject_keyword_styles() (+10 more)

### Community 20 - "build_nakimov_harvard_cv_ru.py"
Cohesion: 0.20
Nodes (20): Document, _add_rich_paragraph(), b(), build_docx(), build_pdf(), hr(), main(), make_styles() (+12 more)

### Community 21 - "vacancy_fit_advice_service.py"
Cohesion: 0.15
Nodes (18): infer_target_role(), Целевая роль для cover letter по заголовку вакансии (всегда непустая строка)., _fit_context_json(), generate_vacancy_fit_advice(), load_saved_fit_advice(), _normalize_advice(), _parse_advice(), Session (+10 more)

### Community 22 - "profile_service.py"
Cohesion: 0.19
Nodes (18): extract_search_keys(), ProgressCallback, Session, Извлечение ключей поиска из резюме., _apply_profile_data(), create_profile_from_resume(), get_active_profile(), list_profiles() (+10 more)

### Community 23 - "navigation.py"
Cohesion: 0.17
Nodes (17): Тесты resolve_initial_stage., test_resolve_initial_stage_app_when_ready(), test_resolve_initial_stage_honors_input_after_existing_profile(), render_sidebar_brand(), _go_view(), Goal-oriented navigation — user intent, not implementation., render_app_sidebar(), _render_scan_status() (+9 more)

### Community 24 - "cover_letter_service.py"
Cohesion: 0.23
Nodes (16): Exception, AIRouterError, get_match(), Session, Сохранить письмо, не затирая данные матча., save_cover_letter_draft(), save_fit_advice(), upsert_match() (+8 more)

### Community 25 - "geekjob_parser.py"
Cohesion: 0.20
Nodes (12): GeekjobParserAdapter, Vacancy, build_search_url(), _parse_date(), parse_search_page(), parse_vacancy_page(), datetime, _strip_html() (+4 more)

### Community 26 - "Config"
Cohesion: 0.18
Nodes (6): Config, Logger, Общая настройка логирования для CLI-скриптов., Единый формат stdout для scan/match/enrich/daily_update., setup_cli_logging(), Единая сериализация профиля кандидата для AI и UI.

### Community 27 - "init_db"
Cohesion: 0.24
Nodes (15): main(), main(), main(), main(), main(), main(), main(), main() (+7 more)

### Community 28 - "build_nakimov_harvard_cv.py"
Cohesion: 0.29
Nodes (15): build_en(), build_ru(), bullets(), hr(), main(), make_styles(), HRFlowable, Paragraph (+7 more)

### Community 29 - "PageFetcher"
Cohesion: 0.23
Nodes (12): enrich_geekjob_vacancy(), enrich_habr_vacancy(), PageFetcher, Protocol, apply_enrichment(), list_for_enrichment(), Vacancy, VacancyDTO (+4 more)

### Community 30 - "apply_migrations"
Cohesion: 0.19
Nodes (13): alembic_config(), apply_migrations(), Engine, Применение миграций Alembic., Прогон миграций: upgrade head или stamp для legacy БД без alembic_version., ensure_schema(), Engine, Лёгкие миграции схемы без Alembic (legacy; новые изменения — через… (+5 more)

### Community 31 - "cached_profile_id"
Cohesion: 0.26
Nodes (12): cached_profile_id(), clear_data_cache(), Активный профиль: session_state (сайдбар) приоритетнее БД-кэша., get_active_resume_profile_id(), get_active_resume_profile_label(), Выбор профиля резюме в сайдбаре., _clear_stale_advice(), Рекомендации по улучшению резюме на основе рынка. (+4 more)

### Community 32 - "config_loader.py"
Cohesion: 0.22
Nodes (12): load_criteria(), load_criteria_with_browser(), load_sources(), load_yaml(), Path, Единая загрузка YAML-конфигов из config/., Прочитать YAML-файл; пустой файл → {}., criteria.yaml + секция browser из sources.yaml (как в daily_update / enrich). (+4 more)

### Community 33 - "schedule_service.py"
Cohesion: 0.31
Nodes (12): format_dt_msk(), load_schedule(), next_scan_datetime(), next_scan_label(), _parse_time(), datetime, save_schedule(), schedule_timezone() (+4 more)

### Community 34 - "scan_service.py"
Cohesion: 0.27
Nodes (10): get_profile(), label_for(), Protocol, Колбэки прогресса сканирования., ScanProgressFn, _apply_source_toggles(), _enabled_sources(), Session (+2 more)

### Community 35 - "scheduled_job.py"
Cohesion: 0.28
Nodes (11): ProgressCallback, Сканирование + fast match (UI и ручной запуск)., refresh_vacancies(), RefreshResult, ProgressCallback, Session, Полный цикл: scan → match с записью в scan_runs., run_scheduled_update() (+3 more)

### Community 36 - "review.py"
Cohesion: 0.49
Nodes (9): Namespace, cmd_applied(), cmd_letter(), cmd_list(), cmd_show(), cmd_skip(), _fit_score(), main() (+1 more)

### Community 37 - "build_pdf"
Cohesion: 0.44
Nodes (9): build_pdf(), bullet(), main(), prepare_headshot(), Paragraph, ParagraphStyle, Path, register_fonts() (+1 more)

### Community 38 - "list_for_matching"
Cohesion: 0.36
Nodes (8): list_for_matching(), db_session(), fixture, Session, Тесты выборки вакансий для fit-матчинга., test_list_for_matching_prioritizes_scan_ids(), test_list_for_matching_scoped_to_profile(), test_list_for_matching_skips_already_matched()

### Community 39 - "test_match_service.py"
Cohesion: 0.31
Nodes (8): db_session(), profile(), fixture, Session, Тесты compute_fit_match., test_compute_fit_match_persists_score(), test_match_has_analysis_with_gaps(), test_pick_best_match_prefers_fit_dict()

### Community 40 - "HhParserAdapter"
Cohesion: 0.43
Nodes (3): HhParserAdapter, Vacancy, extract_state()

### Community 41 - "match_service.py"
Cohesion: 0.46
Nodes (7): get_vacancy_skills(), batch_fit_match(), compute_fit_match(), Session, Vacancy, Сервис матчинга: единый детерминированный fit score., vacancy_to_json()

### Community 42 - "Ежедневный персональный радар вакансий"
Cohesion: 0.29
Nodes (6): Доставка в Telegram, Ежедневный персональный радар вакансий, Источник вакансий, Карьерный профиль, Локальное состояние, Ранжирование и честность

### Community 43 - "test_scheduled_job.py"
Cohesion: 0.33
Nodes (5): db_session(), fixture, Session, Тесты scheduled_job — импорты и ранний выход без резюме., test_run_scheduled_update_without_resume_returns_early()

### Community 44 - "BaseModel"
Cohesion: 0.53
Nodes (5): BaseModel, CandidateProfileSchema, SalaryEstimate, SearchSuggestions, WorkPreferences

### Community 45 - "Security"
Cohesion: 0.33
Nodes (5): Before pushing, Do not commit, GitHub CLI, Responsible use, Security

### Community 46 - "send_telegram_radar.py"
Cohesion: 0.70
Nodes (4): chunk_text(), load_secrets(), main(), send_message()

### Community 47 - "test_review_cli.py"
Cohesion: 0.67
Nodes (3): _load_review(), Тесты CLI review (session lifecycle)., test_cmd_show_loads_skills_before_session_close()

## Knowledge Gaps
- **46 isolated node(s):** `job-scout`, `install_schedule.sh script`, `setup_github_auth.sh script`, `Today — daily briefing`, `Vacancy — AI Match & cover letter` (+41 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Vacancy` connect `Vacancy` to `select`, `vacancy_repo.py`, `linkedin_jobs.py`, `HhParserAdapter`, `habr_parser.py`, `hh_state.py`, `geekjob_parser.py`, `PageFetcher`?**
  _High betweenness centrality (0.071) - this node is a cross-community bridge._
- **Why does `CandidateProfile` connect `CandidateProfile` to `db/models.py`, `select`, `vacancy_repo.py`, `search_service.py`, `resume_advice_service.py`, `review.py`, `scan_service.py`, `list_for_matching`, `test_match_service.py`, `match_service.py`, `linkedin_outreach_service.py`, `test_scheduled_job.py`, `vacancy_fit_advice_service.py`, `profile_service.py`, `cover_letter_service.py`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Why does `AIRouter` connect `AIRouter` to `db/models.py`, `select`, `search_service.py`, `resume_advice_service.py`, `linkedin_outreach_service.py`, `vacancy_fit_advice_service.py`, `profile_service.py`, `cover_letter_service.py`, `init_db`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `CandidateProfile` (e.g. with `main()` and `migrate_profiles()`) actually correct?**
  _`CandidateProfile` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 53 inferred relationships involving `select` (e.g. with `.get()` and `.set()`) actually correct?**
  _`select` has 53 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `AIRouter` (e.g. with `main()` and `AICacheStore`) actually correct?**
  _`AIRouter` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `AIResult` (e.g. with `AIRouter` and `AIRouterError`) actually correct?**
  _`AIResult` has 7 INFERRED edges - model-reasoned connections that need verification._