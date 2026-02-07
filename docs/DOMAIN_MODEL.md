# Domain Model — Autonomous Content Factory

## Доменные сущности (Postgres)

### 3.1. BRANDS

| Поле | Тип | Описание |
|---|---|---|
| `id` | UUID | PK |
| `name` | str | Название бренда |
| `timezone` | str | Таймзона (e.g. `Europe/Moscow`) |
| `default_locale` | str | Язык контента по умолчанию |
| `niches` | str[] | Ниши бренда |
| `platforms_enabled` | str[] | Включённые платформы |
| `created_at` | datetime | |
| `updated_at` | datetime | |

### 3.2. POLICIES

| Поле | Тип | Описание |
|---|---|---|
| `id` | UUID | PK |
| `brand_id` | UUID | FK → brands |
| `forbidden_topics` | str[] | Запрещённые темы |
| `forbidden_claim_patterns` | str[] | Паттерны запрещённых утверждений |
| `competitor_rules` | jsonb | Правила упоминания конкурентов |
| `risk_threshold_auto_publish` | int | 0–100, порог для автопубликации |
| `vocabulary` | jsonb | `{preferred, banned, replacements}` |
| `created_at` | datetime | |
| `updated_at` | datetime | |

### 3.3. SOURCES (тренды/референсы)

| Поле | Тип | Описание |
|---|---|---|
| `id` | UUID | PK |
| `platform` | str | Платформа-источник |
| `url` | str | URL контента |
| `author` | str | Автор |
| `transcript` | text | Транскрипт |
| `features` | jsonb | `{hook_type, pacing, overlays, duration}` |
| `cluster_id` | UUID | FK → clusters (nullable) |
| `scores` | jsonb | Оценки различных метрик |
| `ingested_at` | datetime | |

### 3.4. PATTERNS

| Поле | Тип | Описание |
|---|---|---|
| `id` | UUID | PK |
| `brand_id` | UUID | FK → brands |
| `week_bucket` | str | Неделя (e.g. `2025-W23`) |
| `description` | text | Описание паттерна |
| `examples` | jsonb | Примеры |
| `adaptation_rules` | jsonb | Правила адаптации |
| `effectiveness_score` | float | Оценка эффективности |
| `created_at` | datetime | |
| `updated_at` | datetime | |

### 3.5. IDEAS

| Поле | Тип | Описание |
|---|---|---|
| `id` | UUID | PK |
| `brand_id` | UUID | FK → brands |
| `title` | str | Название идеи |
| `angle` | str | Угол подачи |
| `persona` | str | Целевая персона |
| `format` | str | Формат контента |
| `priority_score` | float | 0–100 |
| `risk_score` | float | 0–100 |
| `effort_score` | float | 0–100 |
| `pattern_id` | UUID | FK → patterns (nullable) |
| `status` | enum | См. State Machine |
| `created_at` | datetime | |
| `updated_at` | datetime | |

### 3.6. SCRIPTS

| Поле | Тип | Описание |
|---|---|---|
| `id` | UUID | PK |
| `idea_id` | UUID | FK → ideas |
| `version` | int | Версия сценария |
| `hook_variants` | jsonb | ≥3 вариантов хуков |
| `script_sections` | jsonb | `{hook, body, payoff, cta}` |
| `on_screen_text` | jsonb | `{timecode: text}` |
| `broll_list` | str[] | Список b-roll |
| `qc_status` | enum | `PENDING / APPROVED / REJECTED / REWRITING` |
| `qc_notes` | text | Заметки QC |
| `generation_meta` | jsonb | Мета генерации (модель, tokens, etc.) |
| `created_at` | datetime | |
| `updated_at` | datetime | |

### 3.7. ASSETS

| Поле | Тип | Описание |
|---|---|---|
| `id` | UUID | PK |
| `script_id` | UUID | FK → scripts |
| `type` | str | Тип ассета (video, image, subtitle, thumbnail) |
| `s3_key` | str | Ключ в S3 |
| `specs` | jsonb | Спецификации (resolution, format, etc.) |
| `checksum` | str | SHA-256 |
| `provenance` | jsonb | Происхождение (generated, sourced, etc.) |
| `created_at` | datetime | |

### 3.8. POSTS

| Поле | Тип | Описание |
|---|---|---|
| `id` | UUID | PK |
| `brand_id` | UUID | FK → brands |
| `script_id` | UUID | FK → scripts |
| `platform` | str | Целевая платформа |
| `scheduled_at` | datetime | Запланированное время |
| `published_at` | datetime | Фактическое время публикации |
| `caption` | text | Подпись |
| `hashtags` | str[] | Хэштеги |
| `utm_params` | jsonb | UTM-метки |
| `publish_status` | enum | `DRAFT / SCHEDULED / PUBLISHING / PUBLISHED / FAILED` |
| `url` | str | URL опубликованного контента |
| `created_at` | datetime | |
| `updated_at` | datetime | |

### 3.9. METRICS

| Поле | Тип | Описание |
|---|---|---|
| `id` | UUID | PK |
| `post_id` | UUID | FK → posts |
| `window` | str | `2h / 24h / 72h` |
| `views` | int | Просмотры |
| `watch_time` | float | Среднее время просмотра (сек) |
| `retention` | float | % удержания |
| `ctr` | float | Click-through rate |
| `comments` | int | Кол-во комментариев |
| `shares` | int | Репосты |
| `saves` | int | Сохранения |
| `sentiment` | float | -1.0 ... 1.0 |
| `top_questions` | str[] | Топ вопросы из комментариев |
| `collected_at` | datetime | |

### 3.10. RUNS (audit)

| Поле | Тип | Описание |
|---|---|---|
| `id` | UUID | PK |
| `workflow_id` | str | ID workflow в Temporal |
| `trigger_type` | str | `cron / manual / signal` |
| `started_at` | datetime | |
| `finished_at` | datetime | Nullable |
| `status` | enum | `RUNNING / COMPLETED / FAILED / CANCELLED` |
| `errors` | jsonb | Ошибки (nullable) |

## State Machine: IDEA.status

```
BACKLOG
  → RESEARCHED
    → PLANNED
      → SCRIPTING
        → QC
          → PRODUCING
            → SCHEDULED
              → PUBLISHED
                → LEARNING
                  → ARCHIVED
```

**Правила:**
- Переходы **только** через workflow (никаких прямых UPDATE)
- Каждый переход логируется в RUNS
- Обратные переходы: `QC → SCRIPTING` (rewrite), `NEEDS_APPROVAL → PLANNED` (rejected)
