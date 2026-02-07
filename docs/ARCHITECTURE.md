# Architecture — Autonomous Content Factory

## Высокоуровневая схема

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  FastAPI     │────▶│  Temporal Server  │────▶│  Worker Pool    │
│  (API GW)   │     │  (Orchestrator)   │     │  (Python)       │
└─────────────┘     └──────────────────┘     └─────────────────┘
       │                     │                        │
       ▼                     ▼                        ▼
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Postgres   │     │  Vector DB       │     │  S3 / MinIO     │
│  (State)    │     │  (Embeddings)    │     │  (Media)        │
└─────────────┘     └──────────────────┘     └─────────────────┘
```

## Потоки данных

### 1. Ingestion Flow

```
Cron (6h) → Temporal → ingest_worker
  → fetch trending content from platforms
  → extract transcripts
  → extract features (hook_type, pacing, duration...)
  → cluster similar content
  → store SOURCES + update PATTERNS
```

### 2. Planning Flow

```
Cron (daily) → Temporal → analyze_worker
  → load PATTERNS + SOURCES
  → analyze comments for questions/gaps
  → compare with existing content archive (vector search)
  → generate IDEAS with scores
  → create publishing plan
```

### 3. Generation Flow

```
Idea selected → Temporal → generate_worker
  → load brand POLICY
  → generate script (≥3 hook variants)
  → QC check (automated)
  → auto-rewrite if QC fails (up to N attempts)
  → risk scoring
  → route: auto-publish or NEEDS_APPROVAL
```

### 4. Production Flow

```
Script approved → Temporal → media_worker
  → generate/assemble video assets
  → generate subtitles
  → generate thumbnails
  → upload to S3
  → create ASSETS records
```

### 5. Publishing Flow

```
Scheduled time → Temporal → publish_worker
  → post to platform API
  → verify URL / status
  → retry with backoff on failure
  → log POST record
```

### 6. Learning Flow

```
Timer (2h/24h/72h) → Temporal → metrics_worker
  → fetch metrics from platform API
  → store METRICS
  → compare with baseline
  → update PATTERNS effectiveness_score
  → generate new IDEAS if pattern found
```

## Структура монорепо

```
repo/
├── apps/                    # Запускаемые сервисы
│   ├── api/                 # FastAPI application
│   ├── worker_ingest/       # Temporal worker: сбор трендов
│   ├── worker_analyze/      # Temporal worker: анализ и планирование
│   ├── worker_generate/     # Temporal worker: генерация контента
│   ├── worker_publish/      # Temporal worker: публикация
│   └── worker_metrics/      # Temporal worker: метрики и обучение
├── libs/                    # Общие библиотеки
│   ├── core/                # Конфиги, базовые модели, утилиты
│   ├── db/                  # SQLAlchemy модели, репозитории, миграции
│   ├── llm/                 # Абстракция LLM-провайдеров
│   ├── media/               # Работа с медиа-ассетами
│   ├── scoring/             # PriorityScore, RiskScore
│   └── platform/            # Интеграции с платформами (TikTok, YT, etc.)
├── prompts/                 # Промпт-шаблоны
│   ├── strategist/          # Промпты для анализа и стратегии
│   ├── scriptwriter/        # Промпты для генерации сценариев
│   ├── qc/                  # Промпты для QC-проверки
│   └── community/           # Промпты для ответов на комментарии
├── infra/                   # Инфраструктура
│   ├── docker/              # Dockerfiles
│   └── k8s/                 # Kubernetes manifests
├── migrations/              # Alembic миграции
├── tests/                   # Тесты
│   ├── unit/
│   ├── integration/
│   └── e2e/
└── docs/                    # Документация (этот файл)
```

## Принципы

1. **Stateless API** — FastAPI не хранит состояние сессий
2. **Stateful Workflows** — Temporal хранит состояние каждого workflow
3. **Idempotent Activities** — повторный вызов activity даёт тот же результат
4. **Horizontal Scaling** — каждый worker-тип масштабируется отдельно
5. **Observability First** — structlog + OpenTelemetry + Prometheus на каждом слое
6. **Feature Flags** — любая автоматизация может быть отключена через конфиг
