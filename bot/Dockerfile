# ── Bot: Aiogram Telegram Bot ────────────────────────────────────────────────
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir joblib openai

# Код бота + общие модули
COPY bot/    ./bot/
COPY ml/     ./ml/
COPY app/    ./app/
COPY parser/ ./parser/

RUN mkdir -p logs

CMD ["python", "-m", "bot.main"]
