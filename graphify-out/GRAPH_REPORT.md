# Graph Report - job-scout  (2026-08-02)

## Corpus Check
- 149 files · ~37,114 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 922 nodes · 2493 edges · 45 communities (38 shown, 7 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 190 edges (avg confidence: 0.76)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0f483c74`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- cover_letter_service.py
- vacancy_service/__init__.py
- AIResult
- select
- vacancy_repo.py
- db/models.py
- scan_service.py
- init_db
- CandidateProfile
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
- infer_role_from_title
- cached_profile_id
- profile_filter_service.py
- workflow.py
- enrich_service.py
- test_parsers.py
- test_resume_advice.py
- HhParserAdapter
- test_search_service.py
- install_schedule.sh
- improve_resume.py
- vacancy_fit_advice.py
- src/config.py
- domain/__init__.py
- job-scout

## God Nodes (most connected - your core abstractions)
1. `CandidateProfile` - 52 edges
2. `AIResult` - 29 edges
3. `utc_now()` - 29 edges
4. `AIRouter` - 27 edges
5. `init_db()` - 25 edges
6. `upsert_vacancy()` - 24 edges
7. `get_session()` - 23 edges
8. `session_scope()` - 23 edges
9. `compute_fit()` - 20 edges
10. `render_keywords_step()` - 20 edges

## Surprising Connections (you probably didn't know these)
- `_bootstrap()` --calls--> `session_scope()`  [INFERRED]
  app.py → src/db/session_scope.py
- `_bootstrap()` --calls--> `get_active_profile()`  [INFERRED]
  app.py → src/services/profile_service.py
- `_bootstrap()` --calls--> `get_active_search_settings()`  [INFERRED]
  app.py → src/services/search_service.py
- `main()` --calls--> `snapshot_for_today()`  [INFERRED]
  scripts/daily_update.py → src/analytics.py
- `main()` --calls--> `load_criteria_with_browser()`  [INFERRED]
  scripts/daily_update.py → src/config_loader.py

## Import Cycles
- 3-file cycle: `src/services/vacancy_queries.py -> src/services/vacancy_service/__init__.py -> src/services/vacancy_service/company_listing.py -> src/services/vacancy_queries.py`
- 3-file cycle: `src/services/vacancy_queries.py -> src/services/vacancy_service/__init__.py -> src/services/vacancy_service/listing.py -> src/services/vacancy_queries.py`

## Communities (45 total, 7 thin omitted)

### Community 0 - "cover_letter_service.py"
Cohesion: 0.06
Nodes (68): get_match(), Session, Сохранить письмо, не затирая данные матча., save_cover_letter_draft(), save_fit_advice(), upsert_match(), get_vacancy_skills(), VacancyMatch (+60 more)

### Community 1 - "vacancy_service/__init__.py"
Cohesion: 0.06
Nodes (65): get_vacancy_by_id(), get_vacancy_tags(), ensure_company_brief(), Session, Краткая AI-справка о компании-работодателе., load_detail(), build_count_by_source_query(), build_list_vacancies_base() (+57 more)

### Community 2 - "AIResult"
Cohesion: 0.07
Nodes (22): Config, Exception, AIRouter, AIRouterError, Any, Session, AICacheStore, Session (+14 more)

### Community 3 - "select"
Cohesion: 0.09
Nodes (47): main(), Принудительная очистка кэша. Возвращает число удалённых записей., build_analytics(), Session, Vacancy, _salary_mid(), snapshot_for_today(), get_daily_metrics() (+39 more)

### Community 4 - "vacancy_repo.py"
Cohesion: 0.08
Nodes (48): main(), extract_tags_from_text(), map_work_format(), normalize_skill_name(), normalize_title(), Session, _slug_id(), sync_vacancy_skills() (+40 more)

### Community 5 - "db/models.py"
Cohesion: 0.09
Nodes (41): _database_url(), Alembic environment: metadata from ORM, URL from config., run_migrations_offline(), run_migrations_online(), DeclarativeBase, get_engine(), get_session_factory(), Подключение к БД и фабрика сессий. (+33 more)

### Community 6 - "scan_service.py"
Cohesion: 0.07
Nodes (39): main(), load_criteria(), load_criteria_with_browser(), load_sources(), load_yaml(), Path, Единая загрузка YAML-конфигов из config/., Прочитать YAML-файл; пустой файл → {}. (+31 more)

### Community 7 - "init_db"
Cohesion: 0.09
Nodes (35): Logger, Namespace, main(), main(), main(), cmd_applied(), cmd_letter(), cmd_list() (+27 more)

### Community 8 - "CandidateProfile"
Cohesion: 0.11
Nodes (34): BaseModel, CandidateProfileSchema, SalaryEstimate, SearchSuggestions, WorkPreferences, CandidateProfile, extract_search_keys(), ProgressCallback (+26 more)

### Community 9 - "fit_score.py"
Cohesion: 0.15
Nodes (29): _build_gaps(), _build_risks(), _build_strengths(), _build_summary(), compute_fit(), _domain_fit_score(), _experience_fit_score(), _extract_requirements() (+21 more)

### Community 10 - "components.py"
Cohesion: 0.13
Nodes (26): best_match(), load_vacancy(), Изменение user_status вакансии (application service для UI и скриптов)., Обновить статус вакансии и закоммитить в БД., set_vacancy_status(), Тесты UI-констант (Фаза 3)., test_recommendation_label_full(), test_recommendation_label_short() (+18 more)

### Community 11 - "data.py"
Cohesion: 0.19
Nodes (24): cache_data, Session, Открыть сессию и гарантированно закрыть её. Не делает auto-commit: вызывающий…, session_scope(), cached_company_detail(), cached_company_list(), cached_dashboard_metrics(), cached_experience_chart() (+16 more)

### Community 12 - "task_prompts.py"
Cohesion: 0.12
Nodes (19): apply_channel_guidance(), format_cover_letter_prompt(), Правило вступления: не дублировать площадку при отклике там же., Подстановка без str.format — JSON в профиле не ломает шаблон., _build_analyze_resume_ru(), _build_company_brief(), _build_cover_letter(), _build_improve_resume() (+11 more)

### Community 13 - "parse_setup_page.py"
Cohesion: 0.18
Nodes (19): clear_data_cache(), Прогресс извлечения ключей из резюме., run_extract_with_progress(), _add_item(), apply_draft_to_lists(), _chip_html(), inject_keyword_styles(), Редактор ключей: компактные теги с удалением и добавлением. (+11 more)

### Community 14 - "app.py"
Cohesion: 0.17
Nodes (18): _bootstrap(), _force_public_stub(), main(), Product identity — AI Career Copilot positioning., cached_last_scan(), inject_design_system(), Design tokens and global styles — Linear / Notion inspired., render_sidebar_brand() (+10 more)

### Community 15 - "hh_state.py"
Cohesion: 0.19
Nodes (20): find_vacancy_list(), find_vacancy_view(), format_salary(), _join_labels(), _label_from_dict(), parse_compensation(), parse_published(), parse_search_item() (+12 more)

### Community 16 - "resume_advice_service.py"
Cohesion: 0.17
Nodes (20): work_format_label(), loads_json(), Единая сериализация профиля кандидата для AI и UI., Безопасный json.loads с fallback., JSON для fast/deep match (совпадает с прежним profile_to_json)., Словарь для suggest_filters и настроек поиска., to_match_json(), to_search_dict() (+12 more)

### Community 17 - "fetcher.py"
Cohesion: 0.14
Nodes (8): load_browser_config(), Any, Path, CamoufoxFetcher, create_fetcher(), DrissionFetcher, Единый клиент для загрузки HTML через браузер или requests., RequestsFetcher

### Community 18 - "search_service.py"
Cohesion: 0.22
Nodes (18): main(), SearchSettings, _loads(), filter_keywords(), build_search_draft(), _defaults_from_profile(), get_active_search_settings(), _keywords_from_profile() (+10 more)

### Community 19 - "Vacancy"
Cohesion: 0.15
Nodes (8): setter, BaseAdapter, ManualUrlAdapter, ABC, Vacancy, build_adapters(), DTO для парсеров вакансий., Vacancy

### Community 20 - "infer_role_from_title"
Cohesion: 0.16
Nodes (16): infer_role_from_title(), infer_target_role(), Единые константы и эвристики роли (PM / аналитик / general). Два пути инференса…, Стабильный ключ роли из названия должности., Роль из названия должности; для неизвестных — slug из title., Целевая роль для cover letter по заголовку вакансии (всегда непустая строка)., slug_role(), Vacancy (+8 more)

### Community 21 - "cached_profile_id"
Cohesion: 0.22
Nodes (14): Applications pipeline — job search CRM., render_applications(), match_score_class(), cached_profile_id(), Активный профиль: session_state (сайдбар) приоритетнее БД-кэша., get_active_resume_profile_id(), get_active_resume_profile_label(), Выбор профиля резюме в сайдбаре. (+6 more)

### Community 22 - "profile_filter_service.py"
Cohesion: 0.26
Nodes (14): role_label(), backfill_profile_roles(), backfill_vacancy_settings(), get_active_filter_role(), infer_role_from_settings(), list_profile_filters(), Any, Session (+6 more)

### Community 23 - "workflow.py"
Cohesion: 0.18
Nodes (12): Тесты resolve_initial_stage., test_resolve_initial_stage_app_when_ready(), test_resolve_initial_stage_honors_input_after_existing_profile(), Стартовый экран: загрузка или вставка резюме., Прочитать резюме из session_state (файл или текст)., render_onboarding(), _resolve_resume_content(), Пошаговый сценарий Job Scout. (+4 more)

### Community 24 - "enrich_service.py"
Cohesion: 0.30
Nodes (8): PageFetcher, Protocol, enrich_vacancies(), extract_state(), _enrich_by_source(), enrich_hh_vacancy(), enrich_vacancies_sa(), Session

### Community 25 - "test_parsers.py"
Cohesion: 0.31
Nodes (7): extract_json_array_items(), extract_json_object(), Извлекает объекты вакансий из встроенного JSON на странице поиска Habr., Golden fixtures для чистых парсеров (без сети)., test_extract_json_array_items_habr_style(), test_extract_json_object_from_embedded_state(), test_extract_json_object_returns_none_when_missing()

### Community 26 - "test_resume_advice.py"
Cohesion: 0.28
Nodes (8): compact_market_for_ai(), Сжатый срез рынка для AI (полный market — десятки KB, модель теряет резюме)., _validate_advice(), Тесты resume advice / market collection., test_compact_market_fits_ai_context(), test_validate_accepts_correct_surname(), test_validate_rejects_hallucinated_name(), test_validate_rejects_missing_sections()

### Community 28 - "test_search_service.py"
Cohesion: 0.50
Nodes (4): _profile(), Тесты генерации ключей поиска из профиля., test_defaults_use_profile_title_not_pm_hardcode(), test_settings_to_queries_from_profile_titles()

## Knowledge Gaps
- **2 isolated node(s):** `job-scout`, `install_schedule.sh script`
  These have ≤1 connection - possible missing edges or undocumented components.
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `CandidateProfile` connect `CandidateProfile` to `cover_letter_service.py`, `vacancy_service/__init__.py`, `vacancy_repo.py`, `db/models.py`, `scan_service.py`, `init_db`, `resume_advice_service.py`, `search_service.py`, `test_resume_advice.py`, `test_search_service.py`?**
  _High betweenness centrality (0.065) - this node is a cross-community bridge._
- **Why does `init_db()` connect `init_db` to `select`, `db/models.py`, `scan_service.py`, `CandidateProfile`, `data.py`, `parse_setup_page.py`, `search_service.py`, `cached_profile_id`, `profile_filter_service.py`, `enrich_service.py`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Why does `get_active_profile()` connect `CandidateProfile` to `cover_letter_service.py`, `select`, `scan_service.py`, `init_db`, `parse_setup_page.py`, `app.py`, `resume_advice_service.py`, `cached_profile_id`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Are the 53 inferred relationships involving `select` (e.g. with `.get()` and `.set()`) actually correct?**
  _`select` has 53 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `CandidateProfile` (e.g. with `test_list_companies_groups_vacancies()` and `test_list_vacancies_filters_by_company()`) actually correct?**
  _`CandidateProfile` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `AIResult` (e.g. with `AIRouter` and `AIRouterError`) actually correct?**
  _`AIResult` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `AIRouter` (e.g. with `AICacheStore` and `AIResult`) actually correct?**
  _`AIRouter` has 3 INFERRED edges - model-reasoned connections that need verification._