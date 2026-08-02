# Graph Report - job-scout  (2026-08-02)

## Corpus Check
- 154 files · ~40,025 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 970 nodes · 2584 edges · 50 communities (43 shown, 7 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 196 edges (avg confidence: 0.76)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6bc975ac`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- cover_letter_service.py
- select
- AIResult
- utc_now
- vacancy_repo.py
- db/models.py
- scan_service.py
- get_session
- profile_service.py
- fit_score.py
- components.py
- data.py
- task_prompts.py
- parse_setup_page.py
- app.py
- hh_state.py
- resume_advice_service.py
- fetcher.py
- search_service.py
- Vacancy
- profile_filter_service.py
- cached_profile_id
- profile_migrate.py
- navigation.py
- enrich_service.py
- test_parsers.py
- CandidateProfile
- HhParserAdapter
- test_search_service.py
- install_schedule.sh
- improve_resume.py
- vacancy_fit_advice.py
- src/config.py
- domain/__init__.py
- job-scout
- today_page.py
- extract_state
- BaseModel
- playwright
- setup_agents.sh

## God Nodes (most connected - your core abstractions)
1. `CandidateProfile` - 52 edges
2. `utc_now()` - 30 edges
3. `AIResult` - 29 edges
4. `AIRouter` - 27 edges
5. `upsert_vacancy()` - 26 edges
6. `init_db()` - 25 edges
7. `compute_fit()` - 24 edges
8. `get_session()` - 23 edges
9. `session_scope()` - 23 edges
10. `render_keywords_step()` - 20 edges

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

## Communities (50 total, 7 thin omitted)

### Community 0 - "cover_letter_service.py"
Cohesion: 0.07
Nodes (59): get_match(), Session, Сохранить письмо, не затирая данные матча., save_cover_letter_draft(), save_fit_advice(), upsert_match(), get_vacancy_skills(), VacancyMatch (+51 more)

### Community 1 - "select"
Cohesion: 0.07
Nodes (59): get_vacancy_tags(), ensure_company_brief(), Session, Краткая AI-справка о компании-работодателе., load_detail(), build_count_by_source_query(), build_list_vacancies_base(), build_review_list_query() (+51 more)

### Community 2 - "AIResult"
Cohesion: 0.07
Nodes (22): Config, Exception, AIRouter, AIRouterError, Any, Session, AICacheStore, Session (+14 more)

### Community 3 - "utc_now"
Cohesion: 0.09
Nodes (44): Принудительная очистка кэша. Возвращает число удалённых записей., build_analytics(), Session, Vacancy, _salary_mid(), experience_label(), work_format_label(), get_daily_metrics() (+36 more)

### Community 4 - "vacancy_repo.py"
Cohesion: 0.06
Nodes (55): main(), extract_tags_from_text(), map_work_format(), normalize_skill_name(), normalize_title(), Session, _slug_id(), sync_vacancy_skills() (+47 more)

### Community 5 - "db/models.py"
Cohesion: 0.09
Nodes (39): _database_url(), Alembic environment: metadata from ORM, URL from config., run_migrations_offline(), run_migrations_online(), DeclarativeBase, main(), get_engine(), get_session_factory() (+31 more)

### Community 6 - "scan_service.py"
Cohesion: 0.05
Nodes (57): Logger, main(), main(), main(), snapshot_for_today(), Общая настройка логирования для CLI-скриптов., Единый формат stdout для scan/match/enrich/daily_update., setup_cli_logging() (+49 more)

### Community 7 - "get_session"
Cohesion: 0.23
Nodes (18): Namespace, main(), cmd_applied(), cmd_letter(), cmd_list(), cmd_show(), cmd_skip(), _fit_score() (+10 more)

### Community 8 - "profile_service.py"
Cohesion: 0.19
Nodes (19): extract_search_keys(), ProgressCallback, Session, Извлечение ключей поиска из резюме., _apply_profile_data(), create_profile_from_resume(), get_active_profile(), get_profile() (+11 more)

### Community 9 - "fit_score.py"
Cohesion: 0.12
Nodes (37): _build_gaps(), _build_risks(), _build_strengths(), _build_summary(), compute_fit(), _domain_fit_score(), _evidence_score(), _experience_fit_score() (+29 more)

### Community 10 - "components.py"
Cohesion: 0.13
Nodes (28): best_match(), load_vacancy(), Изменение user_status вакансии (application service для UI и скриптов)., Обновить статус вакансии и закоммитить в БД., set_vacancy_status(), Тесты UI-констант (Фаза 3)., test_recommendation_label_full(), test_recommendation_label_short() (+20 more)

### Community 11 - "data.py"
Cohesion: 0.19
Nodes (24): cache_data, Session, Открыть сессию и гарантированно закрыть её. Не делает auto-commit: вызывающий…, session_scope(), cached_company_detail(), cached_company_list(), cached_dashboard_metrics(), cached_experience_chart() (+16 more)

### Community 12 - "task_prompts.py"
Cohesion: 0.12
Nodes (19): apply_channel_guidance(), format_cover_letter_prompt(), Правило вступления: не дублировать площадку при отклике там же., Подстановка без str.format — JSON в профиле не ломает шаблон., _build_analyze_resume_ru(), _build_company_brief(), _build_cover_letter(), _build_improve_resume() (+11 more)

### Community 13 - "parse_setup_page.py"
Cohesion: 0.20
Nodes (17): Прогресс извлечения ключей из резюме., run_extract_with_progress(), _add_item(), apply_draft_to_lists(), _chip_html(), inject_keyword_styles(), Редактор ключей: компактные теги с удалением и добавлением., _remove_at() (+9 more)

### Community 14 - "app.py"
Cohesion: 0.13
Nodes (18): _bootstrap(), _force_public_stub(), main(), Тесты resolve_initial_stage., test_resolve_initial_stage_app_when_ready(), test_resolve_initial_stage_honors_input_after_existing_profile(), render_applications(), Product identity — AI Career Copilot positioning. (+10 more)

### Community 15 - "hh_state.py"
Cohesion: 0.28
Nodes (15): find_vacancy_view(), format_salary(), _join_labels(), _label_from_dict(), parse_compensation(), parse_published(), parse_search_item(), _parse_skills() (+7 more)

### Community 16 - "resume_advice_service.py"
Cohesion: 0.24
Nodes (14): collect_market_requirements(), compact_market_for_ai(), _extract_requirement_lines(), _fallback_resume_from_text(), generate_resume_advice(), _parse_advice_result(), Session, Требования рынка из вакансий активного профиля резюме. (+6 more)

### Community 17 - "fetcher.py"
Cohesion: 0.14
Nodes (8): load_browser_config(), Any, Path, CamoufoxFetcher, create_fetcher(), DrissionFetcher, Единый клиент для загрузки HTML через браузер или requests., RequestsFetcher

### Community 18 - "search_service.py"
Cohesion: 0.16
Nodes (25): main(), SearchSettings, _loads(), filter_keywords(), loads_json(), Единая сериализация профиля кандидата для AI и UI., Безопасный json.loads с fallback., JSON для fast/deep match (совпадает с прежним profile_to_json). (+17 more)

### Community 19 - "Vacancy"
Cohesion: 0.15
Nodes (8): setter, BaseAdapter, ManualUrlAdapter, ABC, Vacancy, build_adapters(), DTO для парсеров вакансий., Vacancy

### Community 20 - "profile_filter_service.py"
Cohesion: 0.10
Nodes (33): infer_role_from_title(), infer_target_role(), Единые константы и эвристики роли (PM / аналитик / general). Два пути инференса…, Стабильный ключ роли из названия должности., Роль из названия должности; для неизвестных — slug из title., Целевая роль для cover letter по заголовку вакансии (всегда непустая строка)., role_label(), slug_role() (+25 more)

### Community 21 - "cached_profile_id"
Cohesion: 0.33
Nodes (8): Applications pipeline — job search CRM., cached_profile_id(), Активный профиль: session_state (сайдбар) приоритетнее БД-кэша., get_active_resume_profile_id(), get_active_resume_profile_label(), _clear_stale_advice(), Рекомендации по улучшению резюме на основе рынка., render_resume_advice()

### Community 22 - "profile_migrate.py"
Cohesion: 0.23
Nodes (14): _backfill_vacancy_profile_ids(), _default_profile_id(), ensure_profile_schema(), _ensure_vacancy_profile_scoped_uniques(), _has_legacy_global_vacancy_uniques(), Engine, Миграция схемы под изолированные профили резюме., Rebuild vacancies without global UNIQUE(url)/(source,id) — identity is per… (+6 more)

### Community 23 - "navigation.py"
Cohesion: 0.20
Nodes (16): cached_last_scan(), cached_schedule_summary(), render_sidebar_brand(), _go_view(), Goal-oriented navigation — user intent, not implementation., render_app_sidebar(), _render_scan_status(), render_setup_sidebar() (+8 more)

### Community 24 - "enrich_service.py"
Cohesion: 0.27
Nodes (8): main(), PageFetcher, Protocol, enrich_vacancies(), _enrich_by_source(), enrich_hh_vacancy(), enrich_vacancies_sa(), Session

### Community 25 - "test_parsers.py"
Cohesion: 0.31
Nodes (7): extract_json_array_items(), extract_json_object(), Извлекает объекты вакансий из встроенного JSON на странице поиска Habr., Golden fixtures для чистых парсеров (без сети)., test_extract_json_array_items_habr_style(), test_extract_json_object_from_embedded_state(), test_extract_json_object_returns_none_when_missing()

### Community 26 - "CandidateProfile"
Cohesion: 0.16
Nodes (20): CandidateProfile, Делегирует в cover_letter_context — формат v8 не меняется., to_cover_letter_json(), _validate_advice(), Тесты resume advice / market collection., test_extract_requirement_lines_finds_bullets(), test_validate_accepts_correct_surname(), test_validate_rejects_hallucinated_name() (+12 more)

### Community 27 - "HhParserAdapter"
Cohesion: 0.16
Nodes (11): HhParserAdapter, datetime, Vacancy, Client-side age filter. Undated rows are kept when HH already got search_period., find_vacancy_list(), Тесты параметров поиска hh_parser., test_fetch_records_page_errors(), test_search_params_include_week_period() (+3 more)

### Community 28 - "test_search_service.py"
Cohesion: 0.29
Nodes (7): _normalize_hh_queries(), Ensure cached DB queries always carry search_period (default 7 days)., _profile(), Тесты генерации ключей поиска из профиля., test_defaults_use_profile_title_not_pm_hardcode(), test_normalize_hh_queries_injects_search_period(), test_settings_to_queries_from_profile_titles()

### Community 45 - "today_page.py"
Cohesion: 0.24
Nodes (8): Прогресс парсинга вакансий., run_parse_with_progress(), Flash messages for scan results that survive st.rerun()., render_scan_flash(), store_scan_flash(), _go(), Today — daily career briefing (home)., render_today()

### Community 46 - "extract_state"
Cohesion: 0.28
Nodes (8): extract_state(), Parse embedded HH Lux state. Returns None if missing or invalid JSON., Golden fixtures для HH state parser., test_extract_state_returns_none_on_broken_json(), test_extract_state_returns_none_when_missing(), test_extract_state_unescapes_html_entities(), test_format_salary_range(), test_parse_search_item_maps_core_fields()

### Community 47 - "BaseModel"
Cohesion: 0.53
Nodes (5): BaseModel, CandidateProfileSchema, SalaryEstimate, SearchSuggestions, WorkPreferences

### Community 48 - "playwright"
Cohesion: 0.50
Nodes (3): playwright, npx, @playwright/mcp

## Knowledge Gaps
- **5 isolated node(s):** `npx`, `@playwright/mcp`, `job-scout`, `install_schedule.sh script`, `setup_agents.sh script`
  These have ≤1 connection - possible missing edges or undocumented components.
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `CandidateProfile` connect `CandidateProfile` to `cover_letter_service.py`, `select`, `vacancy_repo.py`, `db/models.py`, `scan_service.py`, `get_session`, `profile_service.py`, `resume_advice_service.py`, `search_service.py`, `test_search_service.py`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **Why does `init_db()` connect `db/models.py` to `select`, `scan_service.py`, `get_session`, `profile_service.py`, `data.py`, `parse_setup_page.py`, `today_page.py`, `search_service.py`, `profile_filter_service.py`, `cached_profile_id`, `enrich_service.py`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Why does `Vacancy` connect `Vacancy` to `HhParserAdapter`, `vacancy_repo.py`, `profile_filter_service.py`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Are the 54 inferred relationships involving `select` (e.g. with `.get()` and `.set()`) actually correct?**
  _`select` has 54 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `CandidateProfile` (e.g. with `test_list_companies_groups_vacancies()` and `test_list_vacancies_filters_by_company()`) actually correct?**
  _`CandidateProfile` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `utc_now()` (e.g. with `test_count_new_vacancies_by_scraped_at()` and `test_upsert_vacancy_recovers_from_url_conflict()`) actually correct?**
  _`utc_now()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `AIResult` (e.g. with `AIRouter` and `AIRouterError`) actually correct?**
  _`AIResult` has 7 INFERRED edges - model-reasoned connections that need verification._