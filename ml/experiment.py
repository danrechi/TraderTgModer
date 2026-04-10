"""
ML Experiment Script — Trader News Classifier
==============================================
Шаг 1: Данные     — синтетический датасет из train.py
Шаг 2: Baseline   — TF-IDF + Logistic Regression
Шаг 3: Логирование — CSV + JSON
Шаг 4: Эксперименты — Naive Bayes, SVM, Random Forest
Шаг 5: Анализ ошибок — confusion matrix + ошибочные примеры
Шаг 6: Финальная модель — лучший классификатор → model.pkl

Запуск: python -m ml.experiment
"""

import os
import json
import csv
import time
import joblib
import warnings
import numpy as np

from datetime import datetime
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold, cross_val_predict
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

warnings.filterwarnings("ignore")

# ── Пути ──────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")
LOG_CSV    = os.path.join(BASE_DIR, "experiment_log.csv")
LOG_JSON   = os.path.join(BASE_DIR, "experiment_log.json")
CONF_TXT   = os.path.join(BASE_DIR, "confusion_matrix.txt")
ERRORS_TXT = os.path.join(BASE_DIR, "error_analysis.txt")

# ── Шаг 1: Данные ─────────────────────────────────────────────────────────────
from ml.train import TRAINING_DATA

TEXTS      = [t for t, _ in TRAINING_DATA]
LABELS     = [l for _, l in TRAINING_DATA]
CATEGORIES = sorted(set(LABELS))

print("=" * 60)
print("ШАГ 1 — ПОДГОТОВКА ДАННЫХ")
print("=" * 60)
print("Всего примеров:", len(TEXTS))
print("Категории (%d):" % len(CATEGORIES))
for cat in CATEGORIES:
    print("  %s: %d примеров" % (cat, LABELS.count(cat)))

# ── TF-IDF векторизатор ───────────────────────────────────────────────────────
TFIDF = TfidfVectorizer(
    analyzer="word",
    ngram_range=(1, 2),
    max_features=5000,
    sublinear_tf=True,
    lowercase=True,
)

# ── Шаг 2 + 4: Все классификаторы ─────────────────────────────────────────────
CLASSIFIERS = {
    "Logistic Regression (Baseline)": LogisticRegression(
        max_iter=1000, C=5.0, solver="lbfgs"
    ),
    "Naive Bayes": MultinomialNB(alpha=0.5),
    "SVM (LinearSVC)": LinearSVC(max_iter=2000, C=1.0),
    "Random Forest": RandomForestClassifier(
        n_estimators=200, random_state=42, n_jobs=-1
    ),
}

# ── Шаг 3: Эксперименты + Логирование ─────────────────────────────────────────
results = []
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

print("\n" + "=" * 60)
print("ШАГ 2-4 — ЭКСПЕРИМЕНТЫ")
print("=" * 60)

for name, clf in CLASSIFIERS.items():
    print("\n[%s]" % name)
    pipe = Pipeline([("tfidf", TFIDF), ("clf", clf)])

    t0     = time.time()
    scores = cross_val_score(pipe, TEXTS, LABELS, cv=cv, scoring="accuracy")
    elapsed = time.time() - t0

    mean_acc  = float(np.mean(scores))
    std_acc   = float(np.std(scores))

    pipe.fit(TEXTS, LABELS)
    preds     = pipe.predict(TEXTS)
    train_acc = float(accuracy_score(LABELS, preds))

    rep      = classification_report(LABELS, preds, output_dict=True)
    macro_f1 = float(rep["macro avg"]["f1-score"])
    macro_pr = float(rep["macro avg"]["precision"])
    macro_re = float(rep["macro avg"]["recall"])

    print("  CV Accuracy : %.4f +/- %.4f" % (mean_acc, std_acc))
    print("  Train Acc   : %.4f" % train_acc)
    print("  Macro F1    : %.4f" % macro_f1)
    print("  Время (CV)  : %.2fs" % elapsed)

    results.append({
        "timestamp":        datetime.now().isoformat(timespec="seconds"),
        "model":            name,
        "cv_accuracy":      round(mean_acc, 4),
        "cv_std":           round(std_acc, 4),
        "train_accuracy":   round(train_acc, 4),
        "macro_f1":         round(macro_f1, 4),
        "macro_precision":  round(macro_pr, 4),
        "macro_recall":     round(macro_re, 4),
        "fit_time_sec":     round(elapsed, 3),
        "n_samples":        len(TEXTS),
        "n_classes":        len(CATEGORIES),
    })

# ── Запись CSV ─────────────────────────────────────────────────────────────────
with open(LOG_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)
print("\n[LOG] CSV: %s" % LOG_CSV)

# ── Запись JSON ────────────────────────────────────────────────────────────────
with open(LOG_JSON, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print("[LOG] JSON: %s" % LOG_JSON)

# ── Шаг 5: Анализ ошибок ──────────────────────────────────────────────────────
best_result = max(results, key=lambda r: r["cv_accuracy"])
best_name   = best_result["model"]
best_pipe   = Pipeline([("tfidf", TFIDF), ("clf", CLASSIFIERS[best_name])])
preds = cross_val_predict(best_pipe, TEXTS, LABELS, cv=cv)
# Обучаем финально для экспорта
best_pipe.fit(TEXTS, LABELS)

print("\n" + "=" * 60)
print("ШАГ 5 — АНАЛИЗ ОШИБОК")
print("Лучшая модель: %s" % best_name)
print("=" * 60)

# Confusion matrix без backslash в f-string
cm      = confusion_matrix(LABELS, preds, labels=CATEGORIES)
col_sep = "True vs Pred"
header  = "%-20s" % col_sep + "".join("%17s" % c[:16] for c in CATEGORIES)
sep     = "-" * len(header)

cm_lines = [header, sep]
for i, cat in enumerate(CATEGORIES):
    row = "%-20s" % cat[:19] + "".join("%17d" % cm[i][j] for j in range(len(CATEGORIES)))
    cm_lines.append(row)

print("\nConfusion Matrix:")
for line in cm_lines:
    print(line)

errors = [
    {"text": TEXTS[i], "true": LABELS[i], "pred": preds[i]}
    for i in range(len(TEXTS))
    if LABELS[i] != preds[i]
]
print("\nОшибочных примеров: %d из %d" % (len(errors), len(TEXTS)))
for e in errors[:5]:
    print("  Текст:    %s" % e["text"])
    print("  Истина: %-20s  Предсказ: %s" % (e["true"], e["pred"]))
    print()

# Сохраняем файлы анализа
with open(ERRORS_TXT, "w", encoding="utf-8") as f:
    f.write("Модель: %s\n" % best_name)
    f.write("Дата: %s\n\n" % datetime.now().isoformat())
    f.write("=== CONFUSION MATRIX ===\n")
    f.write("\n".join(cm_lines) + "\n\n")
    f.write("Ошибочных примеров: %d из %d\n\n" % (len(errors), len(TEXTS)))
    f.write("=== ОШИБОЧНЫЕ ПРИМЕРЫ ===\n")
    for e in errors:
        f.write("Текст:    %s\n" % e["text"])
        f.write("Истина:   %s  /  Предсказ: %s\n\n" % (e["true"], e["pred"]))

with open(CONF_TXT, "w", encoding="utf-8") as f:
    f.write("\n".join(cm_lines))

print("[LOG] Анализ ошибок: %s" % ERRORS_TXT)

# ── Шаг 6: Финальная модель ───────────────────────────────────────────────────
print("\n" + "=" * 60)
print("ШАГ 6 — ФИНАЛЬНАЯ МОДЕЛЬ")
print("=" * 60)
print("Лучший классификатор: %s" % best_name)
print("  CV Accuracy : %s +/- %s" % (best_result["cv_accuracy"], best_result["cv_std"]))
print("  Macro F1    : %s" % best_result["macro_f1"])
joblib.dump(best_pipe, MODEL_PATH)
print("  Сохранён    : %s" % MODEL_PATH)

# ── Итоговая таблица ──────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("ИТОГОВАЯ СВОДКА")
print("=" * 60)
print("%-35s %8s %6s %8s %8s" % ("Модель", "CV Acc", "+/-", "F1", "Время"))
print("-" * 70)
for r in sorted(results, key=lambda x: x["cv_accuracy"], reverse=True):
    marker = " <- лучшая" if r["model"] == best_name else ""
    print("%-35s %8.4f %6.4f %8.4f %7.2fs%s" % (
        r["model"], r["cv_accuracy"], r["cv_std"],
        r["macro_f1"], r["fit_time_sec"], marker
    ))

print("\nВсе артефакты:")
for path in [LOG_CSV, LOG_JSON, ERRORS_TXT, MODEL_PATH]:
    print("  %s" % path)
