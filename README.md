# Trader News Bot — Система автоматической агрегации финансовых новостей

Автоматизированный сервис агрегации, классификации и суммаризации финансовых новостей для Telegram. Система извлекает новости из RSS-лент, классифицирует их по тематике с помощью ML-модели (TF-IDF + SVM), суммаризирует через OpenAI API и публикует в Telegram-чат.

---

## Архитектура

```
┌─────────────────────────────────────────────────┐
│               docker-compose                    │
│                                                 │
│  ┌──────────┐   REST    ┌──────────────────┐   │
│  │ Frontend │ ────────► │  Backend (FastAPI)│   │
│  │ React/   │           │  /health          │   │
│  │  Nginx   │           │  /metrics         │   │
│  └──────────┘           │  /ml/classify     │   │
│       :80               │  /sources, /news  │   │
│                         │  /rules, /auth    │   │
│                         └────────┬─────────┘   │
│                                  │ SQLite       │
│  ┌──────────┐           ┌────────▼─────────┐   │
│  │  TG Bot  │ ────────► │  trader_news.db  │   │
│  │ (aiogram)│           └──────────────────┘   │
│  └──────────┘                                   │
│                         ┌──────────────────┐   │
│                         │  ML Module       │   │
│                         │  ml/model.pkl    │   │
│                         │  (SVM + TF-IDF)  │   │
│                         └──────────────────┘   │
└─────────────────────────────────────────────────┘
```

---

## Быстрый старт (Docker)

### Требования
- [Docker](https://docs.docker.com/get-docker/) ≥ 24.0
- [Docker Compose](https://docs.docker.com/compose/) ≥ 2.20

### 1. Клонировать репозиторий

```bash
git clone https://github.com/danrechi/TraderTgModer.git
cd TraderTgModer
```

### 2. Создать `.env`

Скопируйте шаблон и заполните переменные:

```bash
cp .env.example .env
```

```ini
# .env
BOT_TOKEN=<токен от @BotFather>
CHAT_ID=<ID Telegram-чата для публикации новостей>
OPENAI_API_KEY=<ваш ключ от OpenAI>
ADMIN_PASSWORD=<пароль для входа в веб-панель>
SECRET_KEY=<любая случайная строка ≥32 символов>
```

### 3. Запустить всё

```bash
docker-compose up --build
```

После успешной сборки:

| Сервис | URL |
|---|---|
| Веб-панель (React) | http://localhost |
| Backend API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| Health-check | http://localhost:8000/health |
| Метрики | http://localhost:8000/metrics |

---

## Запуск без Docker (для разработки)

### Backend

```bash
python -m venv venv
venv\Scripts\activate       # Windows
pip install -r requirements.txt

# Обучить модель (если нет ml/model.pkl)
python -m ml.train

# Запустить сервер
uvicorn app.main:app --reload
```

### Telegram-бот

```bash
python -m bot.main
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# откроется на http://localhost:5173
```

---

## API — примеры использования

### Классификация новости

```bash
curl -X POST http://localhost:8000/ml/classify \
  -H "Content-Type: application/json" \
  -d '{"text": "Биткоин обновил исторический максимум выше 100 000 долларов"}'
```

```json
{
  "category": "Криптовалюты",
  "confidence": 0.9123,
  "model": "SVM (LinearSVC)",
  "timestamp": "2025-04-10T09:00:00Z"
}
```

### Health-check

```bash
curl http://localhost:8000/health
```

```json
{"status": "ok", "timestamp": "2025-04-10T09:00:00+00:00"}
```

### Метрики нагрузки

```bash
curl http://localhost:8000/metrics
```

```json
{
  "uptime_seconds": 3612.4,
  "total_requests": 847,
  "error_count": 2,
  "error_rate_pct": 0.24,
  "requests_per_endpoint": {
    "/health": 120,
    "/ml/classify": 45,
    "/news": 200
  },
  "collected_at": "2025-04-10T09:01:00+00:00"
}
```

---

## ML-модуль

Обучение проводилось на синтетическом датасете из **401 заголовка** на русском языке по 7 категориям.

### Результаты экспериментов (CV 5-fold)

| Модель | CV Accuracy | Std | Время |
|---|---|---|---|
| **SVM (LinearSVC)** ← выбрана | **57.4%** | ±3.9% | 0.09s |
| Logistic Regression | 54.6% | ±4.6% | 0.60s |
| Naive Bayes | 53.9% | ±5.8% | 0.13s |
| Random Forest | 38.7% | ±4.1% | 2.20s |

Для переобучения модели:

```bash
python -m ml.experiment   # сравнить все алгоритмы
# или быстро:
python -m ml.train        # обучить на SVM и сохранить model.pkl
```

---

## Проверка работы системы

Матрица ошибок, логи инференса и эксперименты сохраняются в:
- `ml/experiment_log.csv` — таблица результатов
- `ml/error_analysis.txt` — разбор ошибок классификации
- `logs/app.log` — все HTTP-запросы
- `logs/inference.log` — каждый вызов `/ml/classify`

---

## Структура проекта

```
FullStack/
├── app/                  # FastAPI backend
│   ├── main.py           # точка входа, middleware, /health, /metrics
│   ├── routers/
│   │   ├── classify.py   # POST /ml/classify — инференс
│   │   ├── news.py
│   │   ├── sources.py
│   │   ├── rules.py
│   │   └── auth.py
│   ├── models.py         # SQLAlchemy ORM
│   ├── crud.py
│   └── database.py
├── bot/                  # Telegram-бот (aiogram)
│   ├── main.py
│   └── Dockerfile
├── frontend/             # React + Vite admin-panel
│   ├── src/
│   ├── Dockerfile
│   └── nginx.conf
├── ml/                   # ML-модуль
│   ├── dataset.py        # 401 обучающих пример
│   ├── train.py          # обучение модели
│   ├── experiment.py     # сравнение алгоритмов
│   ├── classifier.py     # инференс-класс
│   └── model.pkl         # финальная модель (SVM)
├── parser/               # RSS-парсер + дедупликация
│   └── rss_parser.py
├── logs/                 # Рабочие логи (создаётся автоматически)
├── Dockerfile            # backend image
├── docker-compose.yml    # оркестрация
├── .dockerignore
├── .env.example
└── requirements.txt
```

---

## Лицензия

MIT
