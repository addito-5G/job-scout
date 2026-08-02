# Graph Report - job-scout  (2026-08-02)

## Corpus Check
- 185 files · ~71,965 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1241 nodes · 3110 edges · 73 communities (62 shown, 11 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 217 edges (avg confidence: 0.75)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `3f7b6a78`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- utc_now
- VacancyFilters
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
- create_fetcher
- habr_page.py
- Vacancy
- hh_state.py
- app.py
- detail_facade.py
- parse_setup_page.py
- build_nakimov_harvard_cv_ru.py
- vacancy_fit_advice_service.py
- CandidateProfile
- navigation.py
- cover_letter_service.py
- GeekjobParserAdapter
- init_db
- What You Must Do When Invoked
- build_nakimov_harvard_cv.py
- PageFetcher
- db/models.py
- cached_profile_id
- vacancy_service/__init__.py
- schedule_service.py
- select
- get_vacancy_by_id
- infer_target_role
- build_pdf
- today_service.py
- detail.py
- graphify reference: extra exports and benchmark
- recommendation_label
- Ежедневный персональный радар вакансий
- test_company_listing.py
- BaseModel
- Security
- send_telegram_radar.py
- graphify reference: query, path, explain
- test_linkedin_outreach_service.py
- install_schedule.sh
- setup_github_auth.sh
- improve_resume.py
- vacancy_fit_advice.py
- src/config.py
- domain/__init__.py
- job-scout
- test_cover_letter_context.py
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native AGENTS.md integration
- graphify reference: incremental update and cluster-only
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- extraction-spec.md

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
- `_bootstrap()` --calls--> `session_scope()`  [INFERRED]
  app.py → src/db/session_scope.py
- `_bootstrap()` --calls--> `get_active_profile()`  [INFERRED]
  app.py → src/services/profile_service.py
- `_bootstrap()` --calls--> `get_active_search_settings()`  [INFERRED]
  app.py → src/services/search_service.py
- `main()` --calls--> `get_session()`  [INFERRED]
  scripts/bootstrap_profile.py → src/db/engine.py
- `main()` --calls--> `init_db()`  [INFERRED]
  scripts/bootstrap_profile.py → src/db/engine.py

## Import Cycles
- 3-file cycle: `src/services/vacancy_queries.py -> src/services/vacancy_service/__init__.py -> src/services/vacancy_service/company_listing.py -> src/services/vacancy_queries.py`
- 3-file cycle: `src/services/vacancy_queries.py -> src/services/vacancy_service/__init__.py -> src/services/vacancy_service/listing.py -> src/services/vacancy_queries.py`

## Communities (73 total, 11 thin omitted)

### Community 0 - "utc_now"
Cohesion: 0.05
Nodes (59): main(), build_analytics(), Session, Vacancy, _salary_mid(), snapshot_for_today(), load_criteria(), load_criteria_with_browser() (+51 more)

### Community 1 - "VacancyFilters"
Cohesion: 0.14
Nodes (21): build_list_vacancies_base(), list_vacancy_filter_conditions(), Any, ColumnElement, SQLAlchemy query builders для списков и агрегатов вакансий., Базовый SELECT для списка вакансий с join на единый fit match., Условия WHERE для list_vacancies., _company_group_query() (+13 more)

### Community 2 - "vacancy_repo.py"
Cohesion: 0.07
Nodes (60): backup_db(), _columns(), drop_legacy_tables(), _fetch_all(), is_legacy_schema(), main(), migrate_ai_cache(), migrate_matches() (+52 more)

### Community 3 - "search_service.py"
Cohesion: 0.05
Nodes (76): main(), main(), SearchSettings, infer_role_from_title(), Стабильный ключ роли из названия должности., Роль из названия должности; для неизвестных — slug из title., role_label(), slug_role() (+68 more)

### Community 4 - "resume_advice_service.py"
Cohesion: 0.16
Nodes (21): work_format_label(), collect_market_requirements(), compact_market_for_ai(), _extract_requirement_lines(), _fallback_resume_from_text(), generate_resume_advice(), _parse_advice_result(), Session (+13 more)

### Community 5 - "NextMove"
Cohesion: 0.04
Nodes (44): 1. Clone & install, 2. Configure, 3. Initialize DB & run UI, 4. First-time setup (CLI), AI: free by design, Author, CLI reference, Database migrations (Alembic) (+36 more)

### Community 6 - "AIRouter"
Cohesion: 0.07
Nodes (22): Config, Exception, AIRouter, AIRouterError, Any, Session, AICacheStore, Session (+14 more)

### Community 7 - "linkedin_jobs.py"
Cohesion: 0.10
Nodes (28): LinkedinJobUrlAdapter, LinkedinParserAdapter, Vacancy, Импорт одной вакансии по публичному URL (без авторизации)., Публичный guest API LinkedIn Jobs — без логина и cookies пользователя., build_search_url(), canonical_job_url(), _description_from_jsonld() (+20 more)

### Community 8 - "task_prompts.py"
Cohesion: 0.09
Nodes (24): apply_channel_guidance(), format_cover_letter_prompt(), Правило вступления: не дублировать площадку при отклике там же., Подстановка без str.format — JSON в профиле не ломает шаблон., format_linkedin_outreach_prompt(), _build_analyze_resume_ru(), _build_company_brief(), _build_cover_letter() (+16 more)

### Community 9 - "render_detail"
Cohesion: 0.15
Nodes (26): best_match(), Обновить статус вакансии и закоммитить в БД., set_vacancy_status(), Applications pipeline — job search CRM., render_applications(), format_salary(), match_score_badge(), match_score_class() (+18 more)

### Community 10 - "fit_score.py"
Cohesion: 0.15
Nodes (29): _build_gaps(), _build_risks(), _build_strengths(), _build_summary(), compute_fit(), _domain_fit_score(), _experience_fit_score(), _extract_requirements() (+21 more)

### Community 11 - "linkedin_outreach_service.py"
Cohesion: 0.18
Nodes (20): first_name_from(), _is_analyst_tool(), _is_pm_relevant(), match_context_for_cover_letter(), profile_for_cover_letter_json(), profile_for_outreach_json(), Контекст профиля для LinkedIn outreach — факты + углы позиционирования., role_title_for_letter() (+12 more)

### Community 12 - "data.py"
Cohesion: 0.23
Nodes (19): cache_data, Session, Открыть сессию и гарантированно закрыть её. Не делает auto-commit: вызывающий…, session_scope(), cached_dashboard_metrics(), cached_experience_chart(), cached_match_buckets(), cached_opportunity_list() (+11 more)

### Community 13 - "create_fetcher"
Cohesion: 0.20
Nodes (7): FetchReport, main(), _probe(), CamoufoxFetcher, create_fetcher(), DrissionFetcher, RequestsFetcher

### Community 14 - "habr_page.py"
Cohesion: 0.14
Nodes (17): Vacancy, _parse_habr_date(), parse_search_page(), parse_vacancy_json_ld(), parse_vacancy_page(), datetime, Fallback: некоторые страницы содержат JSON-LD., _strip_html() (+9 more)

### Community 15 - "Vacancy"
Cohesion: 0.13
Nodes (11): setter, BaseAdapter, HabrRssAdapter, ManualUrlAdapter, ABC, Vacancy, HabrParserAdapter, build_adapters() (+3 more)

### Community 16 - "hh_state.py"
Cohesion: 0.14
Nodes (23): HhParserAdapter, Vacancy, extract_state(), find_vacancy_list(), find_vacancy_view(), format_salary(), _join_labels(), _label_from_dict() (+15 more)

### Community 17 - "app.py"
Cohesion: 0.13
Nodes (19): _bootstrap(), _force_public_stub(), main(), Тесты resolve_initial_stage., test_resolve_initial_stage_app_when_ready(), test_resolve_initial_stage_honors_input_after_existing_profile(), Product identity — AI Career Copilot positioning., inject_design_system() (+11 more)

### Community 18 - "detail_facade.py"
Cohesion: 0.18
Nodes (18): fit_to_match_dict(), generate_fit_advice(), generate_letter(), generate_outreach(), load_profile(), load_vacancy(), people_search_url(), Session (+10 more)

### Community 19 - "parse_setup_page.py"
Cohesion: 0.15
Nodes (23): clear_data_cache(), Прогресс извлечения ключей из резюме., run_extract_with_progress(), _add_item(), apply_draft_to_lists(), _chip_html(), inject_keyword_styles(), Редактор ключей: компактные теги с удалением и добавлением. (+15 more)

### Community 20 - "build_nakimov_harvard_cv_ru.py"
Cohesion: 0.20
Nodes (20): Document, _add_rich_paragraph(), b(), build_docx(), build_pdf(), hr(), main(), make_styles() (+12 more)

### Community 21 - "vacancy_fit_advice_service.py"
Cohesion: 0.17
Nodes (20): get_match(), Session, Сохранить письмо, не затирая данные матча., save_cover_letter_draft(), save_fit_advice(), upsert_match(), VacancyMatch, _fit_context_json() (+12 more)

### Community 22 - "CandidateProfile"
Cohesion: 0.19
Nodes (20): CandidateProfile, extract_search_keys(), ProgressCallback, Session, Извлечение ключей поиска из резюме., Делегирует в cover_letter_context — формат v8 не меняется., to_cover_letter_json(), _apply_profile_data() (+12 more)

### Community 23 - "navigation.py"
Cohesion: 0.36
Nodes (9): cached_last_scan(), render_sidebar_brand(), _go_view(), Goal-oriented navigation — user intent, not implementation., render_app_sidebar(), _render_scan_status(), render_setup_sidebar(), render_resume_upload_sidebar() (+1 more)

### Community 24 - "cover_letter_service.py"
Cohesion: 0.24
Nodes (12): _append_contacts(), format_contacts_block(), generate_cover_letter(), _get_match_for_letter(), normalize_cover_letter(), _normalize_letter(), Session, Vacancy (+4 more)

### Community 25 - "GeekjobParserAdapter"
Cohesion: 0.18
Nodes (12): GeekjobParserAdapter, Vacancy, build_search_url(), _parse_date(), parse_search_page(), parse_vacancy_page(), datetime, _strip_html() (+4 more)

### Community 26 - "init_db"
Cohesion: 0.11
Nodes (27): Logger, Namespace, main(), main(), main(), cmd_applied(), cmd_letter(), cmd_list() (+19 more)

### Community 27 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native AGENTS.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 28 - "build_nakimov_harvard_cv.py"
Cohesion: 0.29
Nodes (15): build_en(), build_ru(), bullets(), hr(), main(), make_styles(), HRFlowable, Paragraph (+7 more)

### Community 29 - "PageFetcher"
Cohesion: 0.19
Nodes (13): enrich_geekjob_vacancy(), enrich_habr_vacancy(), load_browser_config(), Any, Path, PageFetcher, Protocol, Единый клиент для загрузки HTML через браузер или requests. (+5 more)

### Community 30 - "db/models.py"
Cohesion: 0.07
Nodes (48): _database_url(), Alembic environment: metadata from ORM, URL from config., run_migrations_offline(), run_migrations_online(), DeclarativeBase, get_engine(), get_session_factory(), Подключение к БД и фабрика сессий. (+40 more)

### Community 31 - "cached_profile_id"
Cohesion: 0.30
Nodes (9): cached_profile_id(), Активный профиль: session_state (сайдбар) приоритетнее БД-кэша., get_active_resume_profile_id(), get_active_resume_profile_label(), Выбор профиля резюме в сайдбаре., _clear_stale_advice(), Рекомендации по улучшению резюме на основе рынка., render_resume_advice() (+1 more)

### Community 32 - "vacancy_service/__init__.py"
Cohesion: 0.27
Nodes (13): build_count_by_source_query(), build_review_list_query(), Select, Сервис вакансий — публичный API (re-export подмодулей)., count_vacancies_by_source(), get_salary_bounds(), list_all_tags(), list_for_review() (+5 more)

### Community 33 - "schedule_service.py"
Cohesion: 0.31
Nodes (12): format_dt_msk(), load_schedule(), next_scan_datetime(), next_scan_label(), _parse_time(), datetime, save_schedule(), schedule_timezone() (+4 more)

### Community 34 - "select"
Cohesion: 0.38
Nodes (13): experience_distribution(), get_metrics(), match_score_buckets(), Session, Vacancy, _salary_mid(), _scope(), source_distribution() (+5 more)

### Community 35 - "get_vacancy_by_id"
Cohesion: 0.27
Nodes (10): get_vacancy_by_id(), ensure_company_brief(), Session, Краткая AI-справка о компании-работодателе., Session, VacancyDTO, Запись вакансий: upsert, статус, cover letter., save_vacancy_cover_letter() (+2 more)

### Community 36 - "infer_target_role"
Cohesion: 0.21
Nodes (10): infer_target_role(), Единые константы и эвристики роли (PM / аналитик / general). Два пути инференса…, Целевая роль для cover letter по заголовку вакансии (всегда непустая строка)., Тесты доменной логики ролей., test_infer_role_from_title_analyst(), test_infer_role_from_title_pm(), test_infer_role_from_title_unknown(), test_infer_target_role_general() (+2 more)

### Community 37 - "build_pdf"
Cohesion: 0.44
Nodes (9): build_pdf(), bullet(), main(), prepare_headshot(), Paragraph, ParagraphStyle, Path, register_fonts() (+1 more)

### Community 38 - "today_service.py"
Cohesion: 0.38
Nodes (10): get_last_scan_run(), vacancy_profile_scope(), _application_counts(), build_today_briefing(), _count_excellent_matches(), _greeting_name(), Session, Daily briefing — «What should I do today to get hired?» (+2 more)

### Community 39 - "detail.py"
Cohesion: 0.16
Nodes (18): count_vacancies(), get_vacancy_skills(), get_vacancy_tags(), Session, load_detail(), get_vacancy_detail(), Session, Детальная карточка вакансии. (+10 more)

### Community 40 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 41 - "recommendation_label"
Cohesion: 0.39
Nodes (6): Тесты UI-констант (Фаза 3)., test_recommendation_label_full(), test_recommendation_label_short(), test_recommendation_label_unknown_passthrough(), Подписи рекомендаций AI-match для UI., recommendation_label()

### Community 42 - "Ежедневный персональный радар вакансий"
Cohesion: 0.29
Nodes (6): Доставка в Telegram, Ежедневный персональный радар вакансий, Источник вакансий, Карьерный профиль, Локальное состояние, Ранжирование и честность

### Community 43 - "test_company_listing.py"
Cohesion: 0.38
Nodes (6): db_session(), fixture, Session, Тесты группировки вакансий по компаниям., test_list_companies_groups_vacancies(), test_list_vacancies_filters_by_company()

### Community 44 - "BaseModel"
Cohesion: 0.53
Nodes (5): BaseModel, CandidateProfileSchema, SalaryEstimate, SearchSuggestions, WorkPreferences

### Community 45 - "Security"
Cohesion: 0.33
Nodes (5): Before pushing, Do not commit, GitHub CLI, Responsible use, Security

### Community 46 - "send_telegram_radar.py"
Cohesion: 0.70
Nodes (4): chunk_text(), load_secrets(), main(), send_message()

### Community 47 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 66 - "test_cover_letter_context.py"
Cohesion: 0.47
Nodes (5): _profile(), Тесты контекста cover letter (без вызова AI)., test_first_name_extracts_first_token(), test_profile_for_cover_letter_includes_resume_header(), test_profile_for_cover_letter_pm_splits_skills()

### Community 67 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 68 - "graphify reference: commit hook and native AGENTS.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native AGENTS.md integration, graphify reference: commit hook and native AGENTS.md integration

### Community 69 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

## Knowledge Gaps
- **87 isolated node(s):** `job-scout`, `install_schedule.sh script`, `setup_github_auth.sh script`, `Usage`, `What graphify is for` (+82 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Vacancy` connect `Vacancy` to `vacancy_repo.py`, `get_vacancy_by_id`, `linkedin_jobs.py`, `hh_state.py`, `GeekjobParserAdapter`, `PageFetcher`?**
  _High betweenness centrality (0.061) - this node is a cross-community bridge._
- **Why does `CandidateProfile` connect `CandidateProfile` to `utc_now`, `vacancy_repo.py`, `search_service.py`, `resume_advice_service.py`, `test_cover_letter_context.py`, `linkedin_outreach_service.py`, `test_company_listing.py`, `detail_facade.py`, `vacancy_fit_advice_service.py`, `cover_letter_service.py`, `init_db`, `db/models.py`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Why does `PageFetcher` connect `PageFetcher` to `GeekjobParserAdapter`, `init_db`, `create_fetcher`, `Vacancy`?**
  _High betweenness centrality (0.026) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `CandidateProfile` (e.g. with `main()` and `migrate_profiles()`) actually correct?**
  _`CandidateProfile` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 53 inferred relationships involving `select` (e.g. with `.get()` and `.set()`) actually correct?**
  _`select` has 53 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `AIRouter` (e.g. with `main()` and `AICacheStore`) actually correct?**
  _`AIRouter` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `AIResult` (e.g. with `AIRouter` and `AIRouterError`) actually correct?**
  _`AIResult` has 7 INFERRED edges - model-reasoned connections that need verification._