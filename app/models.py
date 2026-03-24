from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from app.database import Base


class Source(Base):
    """RSS-источник новостей"""
    __tablename__ = "sources"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(255), nullable=False)
    url        = Column(String(500), nullable=False, unique=True)
    is_active  = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Rule(Base):
    """Правило антиспам-фильтрации"""
    __tablename__ = "rules"

    id         = Column(Integer, primary_key=True, index=True)
    type       = Column(String(50),  nullable=False)   # keyword / regex / link
    pattern    = Column(String(500), nullable=False)
    action     = Column(String(50),  nullable=False, default="delete")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class NewsItem(Base):
    """Новостная статья из RSS-ленты"""
    __tablename__ = "news"

    id           = Column(Integer, primary_key=True, index=True)
    title        = Column(String(500),  nullable=False)
    url          = Column(String(1000), nullable=False, unique=True)
    source_name  = Column(String(255),  nullable=True)
    published_at = Column(String(100),  nullable=True)
    category     = Column(String(100),  nullable=True, default="Общее")  # ML-классификация
    content      = Column(Text,         nullable=True)                    # краткая выжимка
    fetched_at   = Column(DateTime(timezone=True), server_default=func.now())
    published_to_chat = Column(Boolean, default=False)                   # уже опубликовано в Telegram


class User(Base):
    """Администратор системы"""
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    username        = Column(String(100), nullable=False, unique=True)
    hashed_password = Column(String(255), nullable=False)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
