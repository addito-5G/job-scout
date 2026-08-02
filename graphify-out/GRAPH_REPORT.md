# Graph Report - job-scout  (2026-08-02)

## Corpus Check
- 167 files · ~45,007 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1099 nodes · 2859 edges · 56 communities (49 shown, 7 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 201 edges (avg confidence: 0.75)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c1d1723a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- vacancy_service/__init__.py
- db/models.py
- search_service.py
- AIRouter
- Vacancy
- vacancy_repo.py
- NextMove
- task_prompts.py
- render_detail
- fit_score.py
- hh_state.py
- resume_advice_service.py
- profile_service.py
- parse_setup_page.py
- fetcher.py
- cover_letter_context.py
- data.py
- habr_page.py
- navigation.py
- app.py
- scheduled_job.py
- CandidateProfile
- cover_letter_service.py
- geekjob_parser.py
- PageFetcher
- config_loader.py
- repositories/__init__.py
- select
- vacancy_fit_advice_service.py
- schedule_service.py
- cached_profile_id
- linkedin_outreach_service.py
- infer_target_role
- today_service.py
- list_for_matching
- normalize_outreach
- recommendation_label
- test_scheduled_job.py
- Security
- HabrParserAdapter
- install_schedule.sh
- improve_resume.py
- vacancy_fit_advice.py
- src/config.py
- domain/__init__.py
- job-scout

## God Nodes (most connected - your core abstractions)
1. `CandidateProfile` - 56 edges
2. `AIRouter` - 29 edges
3. `AIResult` - 29 edges
4. `utc_now()` - 29 edges
5. `init_db()` - 25 edges
6. `upsert_vacancy()` - 24 edges
7. `get_session()` - 23 edges
8. `session_scope()` - 23 edges
9. `Vacancy` - 22 edges
10. `render_keywords_step()` - 22 edges

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

## Communities (56 total, 7 thin omitted)

### Community 0 - "vacancy_service/__init__.py"
Cohesion: 0.05
Nodes (72): get_vacancy_by_id(), get_vacancy_tags(), ensure_company_brief(), Session, Краткая AI-справка о компании-работодателе., load_detail(), build_count_by_source_query(), build_list_vacancies_base() (+64 more)

### Community 1 - "db/models.py"
Cohesion: 0.05
Nodes (61): _database_url(), Alembic environment: metadata from ORM, URL from config., run_migrations_offline(), run_migrations_online(), DeclarativeBase, Logger, Namespace, main() (+53 more)

### Community 2 - "search_service.py"
Cohesion: 0.06
Nodes (68): main(), main(), SearchSettings, infer_role_from_title(), Стабильный ключ роли из названия должности., Роль из названия должности; для неизвестных — slug из title., role_label(), slug_role() (+60 more)

### Community 3 - "AIRouter"
Cohesion: 0.06
Nodes (26): Config, AIRouter, Any, Session, AICacheStore, Session, Принудительная очистка кэша. Возвращает число удалённых записей., BaseAIProvider (+18 more)

### Community 4 - "Vacancy"
Cohesion: 0.07
Nodes (38): setter, BaseAdapter, HabrRssAdapter, ManualUrlAdapter, ABC, Vacancy, LinkedinJobUrlAdapter, LinkedinParserAdapter (+30 more)

### Community 5 - "vacancy_repo.py"
Cohesion: 0.07
Nodes (49): main(), resolve_database_url(), extract_tags_from_text(), map_work_format(), normalize_skill_name(), normalize_title(), Session, _slug_id() (+41 more)

### Community 6 - "NextMove"
Cohesion: 0.04
Nodes (44): 1. Clone & install, 2. Configure, 3. Initialize DB & run UI, 4. First-time setup (CLI), AI: free by design, Author, CLI reference, Database migrations (Alembic) (+36 more)

### Community 7 - "task_prompts.py"
Cohesion: 0.09
Nodes (24): apply_channel_guidance(), format_cover_letter_prompt(), Правило вступления: не дублировать площадку при отклике там же., Подстановка без str.format — JSON в профиле не ломает шаблон., format_linkedin_outreach_prompt(), _build_analyze_resume_ru(), _build_company_brief(), _build_cover_letter() (+16 more)

### Community 8 - "render_detail"
Cohesion: 0.13
Nodes (29): best_match(), Изменение user_status вакансии (application service для UI и скриптов)., Обновить статус вакансии и закоммитить в БД., set_vacancy_status(), Applications pipeline — job search CRM., render_applications(), format_salary(), match_score_badge() (+21 more)

### Community 9 - "fit_score.py"
Cohesion: 0.14
Nodes (30): _build_gaps(), _build_risks(), _build_strengths(), _build_summary(), compute_fit(), _domain_fit_score(), _experience_fit_score(), _extract_requirements() (+22 more)

### Community 10 - "hh_state.py"
Cohesion: 0.14
Nodes (23): HhParserAdapter, Vacancy, extract_state(), find_vacancy_list(), find_vacancy_view(), format_salary(), _join_labels(), _label_from_dict() (+15 more)

### Community 11 - "resume_advice_service.py"
Cohesion: 0.12
Nodes (25): Единая сериализация профиля кандидата для AI и UI., JSON для fast/deep match (совпадает с прежним profile_to_json)., Словарь для suggest_filters и настроек поиска., to_match_json(), to_search_dict(), collect_market_requirements(), compact_market_for_ai(), _extract_requirement_lines() (+17 more)

### Community 12 - "profile_service.py"
Cohesion: 0.15
Nodes (21): BaseModel, CandidateProfileSchema, SalaryEstimate, SearchSuggestions, WorkPreferences, extract_search_keys(), ProgressCallback, Session (+13 more)

### Community 13 - "parse_setup_page.py"
Cohesion: 0.19
Nodes (17): clear_data_cache(), Прогресс извлечения ключей из резюме., run_extract_with_progress(), _add_item(), apply_draft_to_lists(), _chip_html(), inject_keyword_styles(), Редактор ключей: компактные теги с удалением и добавлением. (+9 more)

### Community 14 - "fetcher.py"
Cohesion: 0.14
Nodes (8): load_browser_config(), Any, Path, CamoufoxFetcher, create_fetcher(), DrissionFetcher, Единый клиент для загрузки HTML через браузер или requests., RequestsFetcher

### Community 15 - "cover_letter_context.py"
Cohesion: 0.17
Nodes (19): first_name_from(), _is_analyst_tool(), _is_pm_relevant(), match_context_for_cover_letter(), profile_for_cover_letter_json(), profile_for_outreach_json(), Контекст профиля для LinkedIn outreach — факты + углы позиционирования., role_title_for_letter() (+11 more)

### Community 16 - "data.py"
Cohesion: 0.24
Nodes (18): cache_data, Session, Открыть сессию и гарантированно закрыть её. Не делает auto-commit: вызывающий…, session_scope(), cached_dashboard_metrics(), cached_experience_chart(), cached_last_scan(), cached_match_buckets() (+10 more)

### Community 17 - "habr_page.py"
Cohesion: 0.17
Nodes (16): _parse_habr_date(), parse_search_page(), parse_vacancy_json_ld(), parse_vacancy_page(), datetime, Fallback: некоторые страницы содержат JSON-LD., _strip_html(), extract_json_array_items() (+8 more)

### Community 18 - "navigation.py"
Cohesion: 0.17
Nodes (17): Тесты resolve_initial_stage., test_resolve_initial_stage_app_when_ready(), test_resolve_initial_stage_honors_input_after_existing_profile(), render_sidebar_brand(), _go_view(), Goal-oriented navigation — user intent, not implementation., render_app_sidebar(), _render_scan_status() (+9 more)

### Community 19 - "app.py"
Cohesion: 0.17
Nodes (14): _bootstrap(), _force_public_stub(), main(), Product identity — AI Career Copilot positioning., inject_design_system(), Design tokens and global styles — Linear / Notion inspired., Стартовый экран: загрузка или вставка резюме., Прочитать резюме из session_state (файл или текст). (+6 more)

### Community 20 - "scheduled_job.py"
Cohesion: 0.21
Nodes (16): finish_scan_run(), get_last_scan_run(), is_scan_running(), Session, start_scan_run(), get_active_profile(), ProgressCallback, Сканирование + fast match (UI и ручной запуск). (+8 more)

### Community 21 - "CandidateProfile"
Cohesion: 0.22
Nodes (18): CandidateProfile, normalize_cover_letter(), _normalize_letter(), Лёгкая постобработка: клише и форматирование. Имя — на стороне AI из резюме., Публичная обёртка над post-processing письма (v8, без изменения логики)., generate_fit_advice(), generate_letter(), generate_outreach() (+10 more)

### Community 22 - "cover_letter_service.py"
Cohesion: 0.23
Nodes (16): Exception, AIRouterError, get_match(), Session, Сохранить письмо, не затирая данные матча., save_cover_letter_draft(), save_fit_advice(), upsert_match() (+8 more)

### Community 23 - "geekjob_parser.py"
Cohesion: 0.20
Nodes (12): GeekjobParserAdapter, Vacancy, build_search_url(), _parse_date(), parse_search_page(), parse_vacancy_page(), datetime, _strip_html() (+4 more)

### Community 24 - "PageFetcher"
Cohesion: 0.24
Nodes (11): main(), enrich_geekjob_vacancy(), enrich_habr_vacancy(), PageFetcher, Protocol, enrich_vacancies(), _enrich_by_source(), enrich_hh_vacancy() (+3 more)

### Community 25 - "config_loader.py"
Cohesion: 0.18
Nodes (14): load_criteria(), load_criteria_with_browser(), load_sources(), load_yaml(), Path, Единая загрузка YAML-конфигов из config/., Прочитать YAML-файл; пустой файл → {}., criteria.yaml + секция browser из sources.yaml (как в daily_update / enrich). (+6 more)

### Community 26 - "repositories/__init__.py"
Cohesion: 0.25
Nodes (13): main(), build_analytics(), Session, Vacancy, _salary_mid(), snapshot_for_today(), get_daily_metrics(), _metrics_row_to_dict() (+5 more)

### Community 27 - "select"
Cohesion: 0.33
Nodes (15): experience_label(), work_format_label(), experience_distribution(), get_metrics(), match_score_buckets(), Session, Vacancy, _salary_mid() (+7 more)

### Community 28 - "vacancy_fit_advice_service.py"
Cohesion: 0.21
Nodes (13): _fit_context_json(), generate_vacancy_fit_advice(), load_saved_fit_advice(), _normalize_advice(), _parse_advice(), Session, Vacancy, AI-рекомендации по резюме под конкретную вакансию (Groq primary). (+5 more)

### Community 29 - "schedule_service.py"
Cohesion: 0.31
Nodes (12): format_dt_msk(), load_schedule(), next_scan_datetime(), next_scan_label(), _parse_time(), datetime, save_schedule(), schedule_timezone() (+4 more)

### Community 30 - "cached_profile_id"
Cohesion: 0.26
Nodes (11): cached_profile_id(), Активный профиль: session_state (сайдбар) приоритетнее БД-кэша., get_active_resume_profile_id(), get_active_resume_profile_label(), Выбор профиля резюме в сайдбаре., _clear_stale_advice(), Рекомендации по улучшению резюме на основе рынка., render_resume_advice() (+3 more)

### Community 31 - "linkedin_outreach_service.py"
Cohesion: 0.24
Nodes (10): get_vacancy_skills(), Генерация сообщения для мягкого входа в LinkedIn (ручная отправка)., batch_fit_match(), compute_fit_match(), Session, Vacancy, Сервис матчинга: единый детерминированный fit score., vacancy_to_json() (+2 more)

### Community 32 - "infer_target_role"
Cohesion: 0.21
Nodes (10): infer_target_role(), Единые константы и эвристики роли (PM / аналитик / general). Два пути инференса…, Целевая роль для cover letter по заголовку вакансии (всегда непустая строка)., Тесты доменной логики ролей., test_infer_role_from_title_analyst(), test_infer_role_from_title_pm(), test_infer_role_from_title_unknown(), test_infer_target_role_general() (+2 more)

### Community 33 - "today_service.py"
Cohesion: 0.32
Nodes (11): ColumnElement, vacancy_profile_scope(), vacancy_scope_condition(), _application_counts(), build_today_briefing(), _count_excellent_matches(), _greeting_name(), Session (+3 more)

### Community 34 - "list_for_matching"
Cohesion: 0.36
Nodes (8): list_for_matching(), db_session(), fixture, Session, Тесты выборки вакансий для fit-матчинга., test_list_for_matching_prioritizes_scan_ids(), test_list_for_matching_scoped_to_profile(), test_list_for_matching_skips_already_matched()

### Community 35 - "normalize_outreach"
Cohesion: 0.39
Nodes (7): normalize_outreach(), Постобработка черновика: имя, запреты, markdown, длина., _Profile, Тесты постобработки LinkedIn outreach., test_normalize_outreach_strips_banned_and_surname(), test_normalize_outreach_trims_markdown(), test_profile_for_outreach_json_includes_summary_and_angles()

### Community 36 - "recommendation_label"
Cohesion: 0.39
Nodes (6): Тесты UI-констант (Фаза 3)., test_recommendation_label_full(), test_recommendation_label_short(), test_recommendation_label_unknown_passthrough(), Подписи рекомендаций AI-match для UI., recommendation_label()

### Community 37 - "test_scheduled_job.py"
Cohesion: 0.33
Nodes (5): db_session(), fixture, Session, Тесты scheduled_job — импорты и ранний выход без резюме., test_run_scheduled_update_without_resume_returns_early()

### Community 38 - "Security"
Cohesion: 0.33
Nodes (5): Before pushing, Do not commit, GitHub CLI, Responsible use, Security

## Knowledge Gaps
- **40 isolated node(s):** `job-scout`, `install_schedule.sh script`, `Today — daily briefing`, `Vacancy — AI Match & cover letter`, `Market — Market Insights` (+35 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Vacancy` connect `Vacancy` to `vacancy_service/__init__.py`, `vacancy_repo.py`, `HabrParserAdapter`, `hh_state.py`, `geekjob_parser.py`, `PageFetcher`?**
  _High betweenness centrality (0.076) - this node is a cross-community bridge._
- **Why does `CandidateProfile` connect `CandidateProfile` to `vacancy_service/__init__.py`, `db/models.py`, `search_service.py`, `normalize_outreach`, `list_for_matching`, `test_scheduled_job.py`, `vacancy_repo.py`, `resume_advice_service.py`, `profile_service.py`, `cover_letter_context.py`, `scheduled_job.py`, `cover_letter_service.py`, `vacancy_fit_advice_service.py`, `linkedin_outreach_service.py`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Why does `init_db()` connect `db/models.py` to `search_service.py`, `parse_setup_page.py`, `data.py`, `scheduled_job.py`, `PageFetcher`, `repositories/__init__.py`, `select`, `cached_profile_id`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `CandidateProfile` (e.g. with `test_list_companies_groups_vacancies()` and `test_list_vacancies_filters_by_company()`) actually correct?**
  _`CandidateProfile` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 53 inferred relationships involving `select` (e.g. with `.get()` and `.set()`) actually correct?**
  _`select` has 53 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `AIRouter` (e.g. with `AICacheStore` and `AIResult`) actually correct?**
  _`AIRouter` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `AIResult` (e.g. with `AIRouter` and `AIRouterError`) actually correct?**
  _`AIResult` has 7 INFERRED edges - model-reasoned connections that need verification._