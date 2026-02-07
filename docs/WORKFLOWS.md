# Workflows — Autonomous Content Factory

## Обзор workflow-процессов

Все workflow реализуются через **Temporal Python SDK**. Каждый workflow — детерминированный, с гарантией продолжения после сбоев.

---

## 5.1. Trend Ingest Workflow

**Триггер:** Cron каждые 6 часов
**Task Queue:** `ingest`

### Шаги:

1. **Fetch Trending** — получить список популярных видео/постов с платформ
2. **Extract Transcripts** — транскрибировать контент (Whisper API / платформенный API)
3. **Extract Features** — извлечь характеристики:
   - `hook_type` (вопрос, шок, статистика, история)
   - `pacing` (быстро, средне, медленно)
   - `overlays` (текст, стикеры, графика)
   - `duration`
4. **Cluster** — кластеризовать по сходству (embedding + DBSCAN/HDBSCAN)
5. **Update Patterns** — обновить/создать записи PATTERNS с актуальными трендами

### Результат:
- Новые записи в `SOURCES`
- Обновлённые `PATTERNS`

---

## 5.2. Gap Mining + Planning Workflow

**Триггер:** Cron ежедневно
**Task Queue:** `analyze`

### Шаги:

1. **Analyze Comments** — собрать комментарии, извлечь вопросы и pain points
2. **Compare Archive** — vector search: найти, что уже покрыто vs что нет
3. **Generate Ideas** — на основе гэпов сгенерировать IDEAS через LLM
4. **Score Ideas** — рассчитать PriorityScore и RiskScore для каждой идеи
5. **Create Publishing Plan** — отсортировать, выбрать топ-N, назначить слоты

### PriorityScore (0–100):
```
0.35 * TrendScore
+ 0.25 * GapScore
+ 0.20 * BrandFit
+ 0.10 * EffortInverse
+ 0.10 * ConversionIntent
```

### RiskScore (0–100):
```
0.30 * ClaimRisk
+ 0.25 * CompetitorRisk
+ 0.15 * PolicyViolation
+ 0.15 * Ambiguity
+ 0.15 * PlatformRisk
```

### Результат:
- Новые записи в `IDEAS` со статусом `PLANNED`
- Обновлённый план публикаций

---

## 5.3. Script Generation Workflow

**Триггер:** Idea.status → SCRIPTING
**Task Queue:** `generate`

### Шаги:

1. **Load Context** — загрузить IDEA + POLICY + brand memory (vector DB)
2. **Generate Script** — LLM генерирует сценарий:
   - ≥3 hook variants
   - Секции: `{hook, body, payoff, cta}`
   - On-screen text с таймкодами
   - B-roll список
3. **QC Check** — автоматическая проверка:
   - Forbidden topics
   - Claim patterns
   - Vocabulary compliance
   - Risk assessment
4. **Auto-rewrite** — если QC не пройден:
   - Rewrite до N попыток (конфигурируемо, default=3)
   - Каждая попытка с конкретными QC notes
5. **Route** — по результатам:
   - `risk_score ≤ threshold` AND `qc_status = APPROVED` → `PRODUCING`
   - Иначе → `NEEDS_APPROVAL` (ждёт ручной сигнал)

### Результат:
- Запись в `SCRIPTS`
- Idea.status → `QC` → `PRODUCING` или `NEEDS_APPROVAL`

---

## 5.4. Production Workflow

**Триггер:** Script.qc_status → APPROVED
**Task Queue:** `media`

### Шаги:

1. **Generate/Assemble Video** — если media pipeline включен
2. **Generate Subtitles** — SRT/VTT из script_sections
3. **Generate Thumbnails** — обложки
4. **Upload to S3** — все ассеты
5. **Create Asset Records** — записи в `ASSETS` с checksums

### Результат:
- Ассеты в S3
- Записи в `ASSETS`
- Idea.status → `SCHEDULED`

---

## 5.5. Publish Workflow

**Триггер:** Наступление `scheduled_at`
**Task Queue:** `publish`

### Шаги:

1. **Pre-publish Check** — финальная проверка правил автопубликации
2. **Post to Platform** — API-вызов платформы
3. **Verify** — проверить URL и статус публикации
4. **Retry** — при ошибке: exponential backoff (max 3 retry)
5. **Log** — обновить POST record

### Правила автопубликации:
- `risk_score ≤ policy.risk_threshold_auto_publish`
- `qc_status = APPROVED`
- Нет unverified claims
- Нет запрещённых упоминаний конкурентов
- Нет гарантий/доходностей/медицинских/юридических обещаний

### Результат:
- Post.publish_status → `PUBLISHED`
- Idea.status → `PUBLISHED`

---

## 5.6. Metrics & Learning Workflow

**Триггер:** Таймеры после публикации — 2h, 24h, 72h
**Task Queue:** `metrics`

### Шаги:

1. **Fetch Metrics** — получить метрики с платформы
2. **Store** — сохранить в `METRICS` с указанием window
3. **Compare Baseline** — сравнить с baseline (средние по бренду/формату)
4. **Update Effectiveness** — обновить `PATTERNS.effectiveness_score`
5. **Generate Follow-up Ideas** — если контент перформит выше baseline:
   - Сгенерировать follow-up IDEAS
   - Предложить серию

### Результат:
- Записи в `METRICS`
- Обновлённые `PATTERNS`
- Опционально новые `IDEAS`
- Idea.status → `LEARNING` → `ARCHIVED`

---

## Temporal Signals

| Signal | Workflow | Действие |
|---|---|---|
| `approve` | Script Generation | Переход в PRODUCING |
| `reject` | Script Generation | Возврат в PLANNED с notes |
| `pause` | Any | Приостановка workflow |
| `resume` | Any | Возобновление |
| `cancel` | Any | Отмена workflow |

## Temporal Timers

| Timer | Workflow | Назначение |
|---|---|---|
| 2h | Metrics | Первый сбор метрик |
| 24h | Metrics | Второй сбор метрик |
| 72h | Metrics | Финальный сбор, learning |
| 6h | Ingest | Периодический сбор трендов |
| 24h | Planning | Ежедневное планирование |
