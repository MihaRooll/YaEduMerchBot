# Используем лёгкий базовый образ с Python 3.11
FROM python:3.11-slim

# Базовые настройки Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Системные зависимости (минимум) + очистка кеша apt
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# 1) Сначала зависимости (для кеширования слоёв)
COPY requirements.txt .
RUN python -m pip install --upgrade pip && pip install -r requirements.txt

# 2) Затем — весь код
COPY . .

# Каталоги под volume'ы (на случай, если не смонтируются)
RUN mkdir -p /app/data /app/logs

# Порт для вебхука (судя по compose — 8443)
EXPOSE 8443

# Точка входа — подстрой при необходимости (например, ["python", "-m", "src.bot"])
CMD ["python", "main.py"]
