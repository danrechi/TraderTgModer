"""
FastAPI application — Trader News Bot

Включает:
- CORS middleware
- Middleware мониторинга (счётчики запросов, ошибок, uptime)
- Логирование всех запросов в logs/app.log
- Эндпоинты /health и /metrics
- Все бизнес-роутеры
"""

import logging
import os
import time
from collections import defaultdict
from datetime import datetime, timezone

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine
from app import models
from app.routers import sources, news, rules, auth as auth_router
from app.routers import classify as classify_router

# ── Создаём таблицы в SQLite при запуске ─────────────────────────────────────
models.Base.metadata.create_all(bind=engine)

# ── Логирование приложения ────────────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("logs/app.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("app")

# ── Внутренние счётчики мониторинга ──────────────────────────────────────────
_START_TIME: float = time.time()
_request_count: int = 0
_error_count: int = 0
_endpoint_counts: dict[str, int] = defaultdict(int)

# ── FastAPI ───────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Trader News Bot",
    description="Backend API для Telegram-бота с классификацией новостей",
    version="1.0.0",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://frontend:80"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Middleware мониторинга ─────────────────────────────────────────────────────
@app.middleware("http")
async def monitoring_middleware(request: Request, call_next):
    global _request_count, _error_count

    _request_count += 1
    endpoint = request.url.path
    _endpoint_counts[endpoint] += 1

    t0 = time.time()
    try:
        response: Response = await call_next(request)
        duration_ms = round((time.time() - t0) * 1000, 1)

        if response.status_code >= 400:
            _error_count += 1
            logger.warning("%s %s → %d (%.1fms)", request.method, endpoint, response.status_code, duration_ms)
        else:
            logger.info("%s %s → %d (%.1fms)", request.method, endpoint, response.status_code, duration_ms)

        return response

    except Exception as exc:
        _error_count += 1
        logger.error("%s %s → UNHANDLED: %s", request.method, endpoint, exc)
        raise


# ── Health-check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["Monitoring"], summary="Проверка доступности сервиса")
def health():
    """Возвращает статус 200, если сервис работает."""
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── Метрики ───────────────────────────────────────────────────────────────────
@app.get("/metrics", tags=["Monitoring"], summary="Метрики нагрузки")
def metrics():
    """
    Возвращает базовые операционные метрики:
    - uptime_seconds — время работы сервера
    - total_requests — всего запросов с момента запуска
    - error_count — запросы с кодом >= 400
    - requests_per_endpoint — разбивка по эндпоинтам
    """
    uptime = round(time.time() - _START_TIME, 1)
    return {
        "uptime_seconds":        uptime,
        "total_requests":        _request_count,
        "error_count":           _error_count,
        "error_rate_pct":        round(_error_count / max(_request_count, 1) * 100, 2),
        "requests_per_endpoint": dict(_endpoint_counts),
        "collected_at":          datetime.now(timezone.utc).isoformat(),
    }


# ── Роутеры ───────────────────────────────────────────────────────────────────
app.include_router(auth_router.router,     prefix="/auth",     tags=["Auth"])
app.include_router(sources.router,         prefix="/sources",  tags=["Sources"])
app.include_router(news.router,            prefix="/news",     tags=["News"])
app.include_router(rules.router,           prefix="/rules",    tags=["Spam Rules"])
app.include_router(classify_router.router, prefix="/ml",       tags=["ML Inference"])