"""
RSS-парсер: получает статьи из всех активных источников,
прогоняет заголовок через ML-классификатор, сохраняет в БД.
Возвращает список новых статей (для последующей публикации ботом).
"""

import feedparser
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app import models
from ml.classifier import NewsClassifier

# Ленивая загрузка классификатора (синглтон на процесс)
_classifier: NewsClassifier | None = None


def get_classifier() -> NewsClassifier:
    global _classifier
    if _classifier is None:
        _classifier = NewsClassifier()
    return _classifier


def _make_summary(entry) -> str:
    """Извлекает краткую выжимку из RSS-записи (первые 200 символов описания)."""
    description = (
        entry.get("summary") or
        entry.get("description") or
        entry.get("content", [{}])[0].get("value", "") if entry.get("content") else ""
    )
    # убираем HTML-теги простым способом
    import re
    clean = re.sub(r"<[^>]+>", "", str(description)).strip()
    return clean[:250] + "..." if len(clean) > 250 else clean


def parse_all_sources(limit_per_source: int = 10) -> list[models.NewsItem]:
    """
    Главная функция парсера.
    - Проходит по всем активным RSS-источникам из БД.
    - Для каждой новой статьи: классифицирует, сохраняет.
    - Возвращает список только что добавленных новостей (published_to_chat=False).
    """
    db: Session = SessionLocal()
    classifier = get_classifier()
    new_items: list[models.NewsItem] = []

    try:
        sources = db.query(models.Source).filter(models.Source.is_active == True).all()

        for source in sources:
            try:
                feed = feedparser.parse(source.url)
                entries = feed.entries[:limit_per_source]

                for entry in entries:
                    url = entry.get("link", "").strip()
                    if not url:
                        continue

                    # Проверяем — такая статья уже есть в БД?
                    exists = db.query(models.NewsItem).filter(
                        models.NewsItem.url == url
                    ).first()
                    if exists:
                        continue

                    title   = entry.get("title", "Без заголовка").strip()
                    summary = _make_summary(entry)
                    pub_at  = entry.get("published") or entry.get("updated") or ""

                    # ML: определяем тематику новости по заголовку
                    category, confidence = classifier.classify_with_proba(title)

                    item = models.NewsItem(
                        title=title,
                        url=url,
                        source_name=source.name,
                        published_at=pub_at,
                        category=category,
                        content=summary,
                        published_to_chat=False,
                    )
                    db.add(item)
                    new_items.append(item)

            except Exception as e:
                print(f"[Parser] Ошибка при парсинге {source.url}: {e}")

        db.commit()

        # Обновляем объекты после commit (чтобы получить id)
        for item in new_items:
            db.refresh(item)

    finally:
        db.close()

    print(f"[Parser] Добавлено новых статей: {len(new_items)}")
    return new_items


def mark_published(item_ids: list[int]) -> None:
    """Помечает статьи как опубликованные в Telegram-чат."""
    if not item_ids:
        return
    db = SessionLocal()
    try:
        db.query(models.NewsItem).filter(
            models.NewsItem.id.in_(item_ids)
        ).update({"published_to_chat": True}, synchronize_session=False)
        db.commit()
    finally:
        db.close()
