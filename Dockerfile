# Dockerfile
FROM python:3.11-slim

# Базовые настройки Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Системные зависимости (минимум) + создание рабочей директории
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Сначала зависимости — для лучшего кеширования
# Если у вас другой файл зависимостей (poetry/requirements-prod.txt) — скорректируйте строку ниже
COPY requirements.txt ./ 
RUN python -m pip install --upgrade pip && pip install -r requirements.txt

# Затем — весь код
COPY . .

# Гарантируем наличие директорий для volume'ов (на случай, если монтирование не произойдёт)
RUN mkdir -p /app/data /app/logs

# Откройте порт, который слушает ваш webhook-сервер (судя по compose — 8443)
EXPOSE 8443

# Если точка входа у вас иная — скорректируйте команду ниже.
# Например: ["python", "-m", "src.bot"] или путь до вашего основного скрипта.
CMD ["python", "main.py"]
