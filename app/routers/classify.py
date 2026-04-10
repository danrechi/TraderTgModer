"""
Инференс-модуль: принимает текст новости, возвращает категорию и уверенность модели.
Каждый запрос логируется в logs/inference.log.

POST /classify
  Body: {"text": "Биткоин установил новый рекорд..."}
  Response: {"category": "Криптовалюты", "confidence": 0.91, "model": "SVM (LinearSVC)", "timestamp": "..."}
"""

import logging
import os
from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from ml.classifier import NewsClassifier

# ── Логирование инференса ─────────────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)

_inf_logger = logging.getLogger("inference")
if not _inf_logger.handlers:
    _inf_logger.setLevel(logging.INFO)
    _handler = logging.FileHandler("logs/inference.log", encoding="utf-8")
    _handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", "%Y-%m-%d %H:%M:%S")
    )
    _inf_logger.addHandler(_handler)

# ── Синглтон классификатора ───────────────────────────────────────────────────
_classifier: NewsClassifier | None = None


def get_classifier() -> NewsClassifier:
    global _classifier
    if _classifier is None:
        _classifier = NewsClassifier()
    return _classifier


# ── Схемы запроса/ответа ──────────────────────────────────────────────────────
class ClassifyRequest(BaseModel):
    text: str


class ClassifyResponse(BaseModel):
    category: str
    confidence: float
    model: str = "SVM (LinearSVC)"
    timestamp: str


# ── Роутер ────────────────────────────────────────────────────────────────────
router = APIRouter()


@router.post("/classify", response_model=ClassifyResponse, summary="Классифицировать новость")
def classify_text(req: ClassifyRequest):
    """
    Принимает заголовок новости и возвращает:
    - **category** — предсказанная тематика
    - **confidence** — уверенность модели (0–1); для SVM всегда 1.0 (нет proba)
    - **timestamp** — UTC-время обработки
    """
    clf = get_classifier()

    # SVM не выдаёт калиброванные вероятности, используем classify
    category = clf.classify(req.text)

    # Пробуем взять уверенность через LR или отдаём 1.0 для SVM
    try:
        _, confidence = clf.classify_with_proba(req.text)
    except Exception:
        confidence = 1.0

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    _inf_logger.info('text="%s" | category=%s | confidence=%.3f', req.text[:120], category, confidence)

    return ClassifyResponse(
        category=category,
        confidence=round(confidence, 4),
        timestamp=ts,
    )
