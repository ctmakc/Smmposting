# Implementation Plan — Autonomous Content Factory

## Фазы реализации

Проект разбит на 6 фаз. Каждая фаза — самодостаточный рабочий инкремент.

---

## Фаза 1: Foundation (Скелет + БД + API)

### Задачи:

1. **Настройка monorepo**
   - pyproject.toml (workspace)
   - ruff + mypy конфиги
   - pytest конфиг
   - Docker base image

2. **libs/core**
   - Конфигурация (Pydantic Settings)
   - Базовые модели (BaseModel, UUIDMixin, TimestampMixin)
   - Structlog setup
   - OpenTelemetry setup

3. **libs/db**
   - SQLAlchemy 2.0 модели для всех 10 сущностей
   - Alembic setup + initial migration
   - Repository pattern (базовый CRUD)

4. **apps/api**
   - FastAPI app setup
   - CRUD endpoints для Brands, Policies
   - Health check
   - Error handling middleware

5. **infra/docker**
   - docker-compose: Postgres, MinIO (S3), API
   - Temporal dev server

### Критерий завершения:
- `docker-compose up` запускает API + Postgres + MinIO
- CRUD для Brands работает через Swagger
- Миграции проходят
- Тесты зелёные

---

## Фаза 2: Temporal + First Workflow

### Задачи:

1. **Temporal integration**
   - Temporal client setup в libs/core
   - Base workflow/activity patterns
   - Worker runner setup

2. **apps/worker_ingest** (упрощённый)
   - Workflow: TrendIngestWorkflow
   - Activity: mock fetch (заглушка для platform API)
   - Activity: store sources

3. **libs/platform**
   - Базовая абстракция PlatformClient
   - Mock implementation для тестов

4. **API: workflow endpoints**
   - POST /workflows/ingest/trigger
   - GET /workflows/{id}/status

### Критерий завершения:
- Temporal workflow запускается через API
- Mock-данные сохраняются в Postgres
- Логи видны в structlog
- Retry работает при имитации сбоя

---

## Фаза 3: LLM Integration + Analysis + Generation

### Задачи:

1. **libs/llm**
   - Абстракция LLM provider (OpenAI, Anthropic, etc.)
   - Prompt template engine (Jinja2)
   - Token counting + cost tracking
   - Structured output parsing

2. **prompts/**
   - Промпты стратегиста (gap analysis)
   - Промпты сценариста (script generation)
   - Промпты QC (quality check)

3. **libs/scoring**
   - PriorityScore calculator
   - RiskScore calculator
   - QC evaluator

4. **apps/worker_analyze**
   - Gap Mining workflow
   - Planning workflow
   - Idea generation activities

5. **apps/worker_generate**
   - Script Generation workflow
   - QC check activity
   - Auto-rewrite loop

### Критерий завершения:
- IDEAS генерируются из PATTERNS + gaps
- SCRIPTS генерируются с ≥3 hook variants
- QC автоматически проверяет сценарии
- Скоринг работает корректно

---

## Фаза 4: Publishing Pipeline

### Задачи:

1. **libs/platform (расширение)**
   - Real platform clients (TikTok, YouTube Shorts, Instagram Reels)
   - Auth flow (OAuth2)
   - Rate limiting
   - Upload API

2. **apps/worker_publish**
   - Publish workflow
   - Pre-publish safety check
   - Post verification
   - Retry with backoff

3. **API: approval endpoints**
   - POST /scripts/{id}/approve
   - POST /scripts/{id}/reject
   - GET /queue/pending-approval

4. **Автопубликация logic**
   - Все правила из Section 7 ТЗ
   - Safety gates

### Критерий завершения:
- Контент публикуется через API платформ
- Approval flow работает
- Safety rules блокируют рискованный контент
- Retry работает при API ошибках

---

## Фаза 5: Metrics & Learning Loop

### Задачи:

1. **apps/worker_metrics**
   - Metrics collection workflow
   - 2h / 24h / 72h timers
   - Baseline calculation
   - Effectiveness scoring

2. **Learning logic**
   - Pattern effectiveness update
   - Follow-up idea generation
   - Strategy adjustment

3. **Vector DB integration**
   - Embeddings для контент-архива
   - Similarity search для anti-repeat
   - Brand memory storage

### Критерий завершения:
- Метрики собираются по таймерам
- Effectiveness обновляется
- Новые идеи генерируются на основе данных
- Anti-repeat работает через vector search

---

## Фаза 6: Observability + Production Hardening

### Задачи:

1. **Observability**
   - Prometheus exporter
   - Grafana dashboards
   - Sentry integration
   - Alert rules

2. **Production**
   - K8s manifests
   - Health checks всех сервисов
   - Graceful shutdown
   - Secret management

3. **Testing**
   - Integration tests для всех workflows
   - E2E test: полный цикл от ingest до metrics
   - Load tests

### Критерий завершения:
- Dashboards показывают все ключевые метрики
- Alerts настроены
- E2E тест проходит
- Система стабильно работает 48+ часов без вмешательства

---

## Приоритет задач в рамках каждой фазы

В каждой фазе работаем по порядку:
1. **Модели данных** → 2. **Бизнес-логика** → 3. **API/Workflow** → 4. **Тесты** → 5. **Docker**

## Текущий статус

| Фаза | Статус |
|---|---|
| Фаза 1: Foundation | DONE (22 tests) |
| Фаза 2: Temporal + First Workflow | DONE (43 tests total, +21 new) |
| Фаза 3: LLM + Analysis + Generation | DONE (76 tests total, +33 new) |
| Фаза 4: Publishing Pipeline | DONE (105 tests total, +29 new) |
| Фаза 5: Metrics & Learning | DONE (138 tests total, +33 new) |
| Фаза 6: Observability + Hardening | DONE (164 tests total, +26 new) |
| Bugfix pass | DONE (186 tests, UUID fixes, Dockerfile, docker-compose) |
| Alembic + Real LLM clients | DONE (240 tests, +54 new) |
