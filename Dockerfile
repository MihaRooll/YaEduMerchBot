FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Зависимости
COPY requirements.txt .
RUN python -m pip install --upgrade pip && pip install -r requirements.txt

# Код
COPY . .

# Папки под данные и логи (на случай, если volume не смонтируется)
RUN mkdir -p /app/data /app/logs

# Никаких EXPOSE/портов — работаем в long polling, наружу ничего не публикуем
CMD ["python", "main.py"]
