# ── Backend: FastAPI + ML ────────────────────────────────────────────────────
FROM python:3.10-slim

WORKDIR /app

# Зависимости системы
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python-зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir joblib openai python-multipart

# Исходный код
COPY app/    ./app/
COPY ml/     ./ml/
COPY parser/ ./parser/

# Том для БД и логов пробрасывается через docker-compose
RUN mkdir -p logs

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
