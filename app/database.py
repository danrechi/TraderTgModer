from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

SQLALCHEMY_DATABASE_URL = "sqlite:///./trader_news.db"

#движок SQLite (check_same_thread=False нужен для FastAPI)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

#фабрика сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#базовый класс для всех ORM-моделей
class Base(DeclarativeBase):
    pass

#зависимость FastAPI: открывает и закрывает сессию на каждый запрос
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
