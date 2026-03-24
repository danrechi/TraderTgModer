"""
Модуль классификации новостей (TF-IDF + LogisticRegression).
Загружает обученную модель из ml/model.pkl;
если файла нет, пробует обучить ее на синтетических данных автоматически.
"""

import os
import joblib
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pkl")

# Катеории и их эмодзи
CATEGORY_EMOJI = {
    "Криптовалюты":    "₿",
    "Акции":           "📈",
    "Экономика":       "🏦",
    "Политика":        "🏛️",
    "Валютный рынок":  "💱",
    "Сырьевые рынки":  "🛢️",
    "Общее":           "📰",
}
CATEGORIES = list(CATEGORY_EMOJI.keys())


class NewsClassifier:
    """
    Классификатор новостей по тематике.
    Использует TF-IDF + LogisticRegression, обученный на синтетических примерах.
    """

    def __init__(self):
        if os.path.exists(MODEL_PATH):
            self.pipeline = joblib.load(MODEL_PATH)
        else:
            # Автоматически обучаем при первом запуске
            print("[ML] model.pkl не найден — запуск обучения...")
            from ml.train import build_pipeline
            self.pipeline = build_pipeline()
            joblib.dump(self.pipeline, MODEL_PATH)
            print("[ML] Модель обучена и сохранена.")

    def classify(self, text: str) -> str:
        """Возвращает категорию новости."""
        if not text or not text.strip():
            return "Общее"
        try:
            return self.pipeline.predict([text])[0]
        except Exception:
            return "Общее"

    def classify_with_proba(self, text: str) -> tuple[str, float]:
        """Возвращает (категория, уверенность 0–1)."""
        if not text or not text.strip():
            return "Общее", 0.0
        proba = self.pipeline.predict_proba([text])[0]
        idx = proba.argmax()
        return self.pipeline.classes_[idx], float(proba[idx])
