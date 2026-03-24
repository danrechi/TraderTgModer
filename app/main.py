from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine
from app import models
from app.routers import sources, news, rules, auth as auth_router

#создаём таблицы в SQLite при запуске (если их ещё нет)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Trader News Bot",
    description="Backend API для Telegram-бота"
)

#CORS — разрешаем запросы от React-фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#подключаем роутеры
app.include_router(auth_router.router, prefix="/auth",    tags=["Auth"])
app.include_router(sources.router,     prefix="/sources", tags=["Sources"])
app.include_router(news.router,        prefix="/news",    tags=["News"])
app.include_router(rules.router,       prefix="/rules",   tags=["Spam Rules"])