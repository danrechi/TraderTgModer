"""
Скрипт обучения ML-классификатора новостей.
Запускается один раз: python -m ml.train
Создаёт файл ml/model.pkl

Используемый подход:
  - Набор синтетических обучающих примеров (заголовки новостей) по 7 категориям
  - Векторизация: TF-IDF по словам + биграммам (работает для рус. и англ. текста)
  - Классификатор: Logistic Regression (быстрый, интерпретируемый)
"""

import os
import joblib
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
import numpy as np

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pkl")

from .dataset import TRAINING_DATA

# ── Обучение модели ──────────────────────────────────────────────────────────

def build_pipeline() -> Pipeline:
    """Создаёт и обучает TF-IDF + LogisticRegression pipeline."""
    texts  = [text for text, _ in TRAINING_DATA]
    labels = [label for _, label in TRAINING_DATA]

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),   # слова и биграммы
            max_features=5000,
            sublinear_tf=True,    # сглаживание TF
            lowercase=True,
        )),
        ("clf", LogisticRegression(
            max_iter=1000,
            C=5.0,
            solver="lbfgs",
        )),
    ])

    pipeline.fit(texts, labels)
    return pipeline


if __name__ == "__main__":
    print("Обучение ML-классификатора новостей...")
    pipeline = build_pipeline()

    # Быстрая кросс-валидация
    texts  = [text for text, _ in TRAINING_DATA]
    labels = [label for _, label in TRAINING_DATA]
    scores = cross_val_score(pipeline, texts, labels, cv=5, scoring="accuracy")
    print(f"Accuracy (5-fold CV): {np.mean(scores):.2f} ± {np.std(scores):.2f}")

    # Сохраняем модель
    joblib.dump(pipeline, MODEL_PATH)
    print(f"Модель сохранена: {MODEL_PATH}")

    # Тестовые предсказания
    test_examples = [
        "Bitcoin упал ниже 30 тысяч долларов",
        "Газпром увеличил дивиденды втрое",
        "ЦБ повысил ставку до 18%",
        "Нефть Brent торгуется у отметки 85 долларов",
        "Рубль укрепился к доллару",
        "Президент подписал бюджет на 2025 год",
    ]
    print("\nТестовые предсказания:")
    for ex in test_examples:
        pred = pipeline.predict([ex])[0]
        prob = pipeline.predict_proba([ex])[0].max()
        print(f"  [{prob:.0%}] {pred:20s} ← {ex}")
