# Техническая документация Docker - YaEduMerchBot

## Спецификации контейнера

### Базовый образ
```dockerfile
FROM python:3.11-slim
```

**Обоснование выбора:**
- Python 3.11 - стабильная версия с хорошей производительностью
- slim образ - уменьшает размер на ~200MB
- Официальный образ с регулярными обновлениями безопасности

### Оптимизации образа
```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
```

**Эффект:**
- `PYTHONDONTWRITEBYTECODE=1` - экономия ~50MB
- `PYTHONUNBUFFERED=1` - немедленный вывод логов
- `PIP_NO_CACHE_DIR=1` - экономия ~100MB
- `PIP_DISABLE_PIP_VERSION_CHECK=1` - ускорение сборки

### Системные зависимости
```dockerfile
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*
```

**Необходимость:**
- `ca-certificates` - для HTTPS запросов к Telegram API
- `curl` - для health checks (если потребуется)

## Размеры образов

### Текущий размер
- **Базовый образ:** ~400MB
- **С зависимостями:** ~450MB
- **С кодом:** ~460MB

### Оптимизация размера
```dockerfile
# Многоэтапная сборка (альтернатива)
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
# ... остальной код
```

**Экономия:** до 100MB

## Переменные окружения

### Обязательные
```bash
BOT_TOKEN=your_telegram_bot_token
MAIN_ADMIN_ID=123456789
```

### Опциональные
```bash
DATABASE_URL=sqlite:///bot.db
ADMIN_IDS=123,456,789
PAYMENT_TOKEN=your_payment_token
LOG_LEVEL=INFO
DEBUG=False
```

### Валидация
```python
# config.py
class Settings(BaseSettings):
    BOT_TOKEN: str = Field(..., description="Telegram Bot Token")
    MAIN_ADMIN_ID: int = Field(..., description="Main Admin Telegram ID")
    
    @validator('BOT_TOKEN')
    def validate_bot_token(cls, v):
        if not v or v == "dummy_token":
            raise ValueError('BOT_TOKEN must be set')
        return v
```

## Volumes и персистентность

### Структура данных
```
/app/
├── data/           # Персистентные данные
│   ├── users.json
│   ├── chats.json
│   ├── inventory.json
│   ├── orders.json
│   └── meta.json
├── logs/           # Логи приложения
└── src/            # Код приложения
```

### Маппинг volumes
```yaml
volumes:
  - bot_data:/app/data      # Docker volume
  - ./logs:/app/logs        # Bind mount
```

**Преимущества:**
- `bot_data` - изоляция и управление Docker
- `./logs` - прямой доступ к логам на хосте

## Сетевая конфигурация

### Текущая архитектура
```
[Telegram API] ←→ [Container:5000] ←→ [Host Network]
```

**Особенности:**
- Нет `EXPOSE` портов
- Работа через long polling
- Изоляция от внешней сети

### Webhook режим (альтернатива)
```dockerfile
EXPOSE 8443
CMD ["python", "main.py", "--webhook"]
```

**Требования:**
- Публичный IP/домен
- SSL сертификат
- Nginx reverse proxy

## Мониторинг и логирование

### Логирование
```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName
        }
        return json.dumps(log_entry)
```

### Health Check
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health')"
```

**Альтернатива для long polling:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD pgrep -f "python main.py" || exit 1
```

## Безопасность

### Текущие меры
- Изоляция через Docker
- Проверка ролей на уровне приложения
- Аудит действий пользователей

### Рекомендации по улучшению
```dockerfile
# Запуск от непривилегированного пользователя
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Ограничение capabilities
RUN setcap -r /usr/bin/python3.11
```

### Secrets management
```yaml
# docker-compose.yml
secrets:
  bot_token:
    file: ./secrets/bot_token.txt
  admin_ids:
    file: ./secrets/admin_ids.txt

services:
  yaedumerchbot:
    secrets:
      - bot_token
      - admin_ids
```

## Производительность

### Оптимизации Python
```dockerfile
# Оптимизация Python
ENV PYTHONOPTIMIZE=1
ENV PYTHONHASHSEED=random

# Увеличение лимитов для long polling
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
```

### Мониторинг ресурсов
```bash
# Мониторинг контейнера
docker stats yaedumerchbot

# Логи производительности
docker logs yaedumerchbot | grep "performance"
```

## Backup и восстановление

### Backup стратегия
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/yaedumerchbot"

# Backup volumes
docker run --rm -v yaedumerchbot:/data -v $BACKUP_DIR:/backup \
    alpine tar czf /backup/data_$DATE.tar.gz -C /data .

# Backup logs
tar czf $BACKUP_DIR/logs_$DATE.tar.gz ./logs/
```

### Восстановление
```bash
#!/bin/bash
# restore.sh
BACKUP_FILE=$1
docker run --rm -v yaedumerchbot:/data -v $BACKUP_FILE:/backup.tar.gz \
    alpine tar xzf /backup.tar.gz -C /data
```

## CI/CD интеграция

### GitHub Actions
```yaml
# .github/workflows/docker-build.yml
name: Docker Build
on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker image
        run: |
          docker build -t yaedumerchbot:${{ github.sha }} .
          docker tag yaedumerchbot:${{ github.sha }} yaedumerchbot:latest
```

### Автоматическое развертывание
```yaml
# .github/workflows/deploy.yml
- name: Deploy to production
  run: |
    echo ${{ secrets.BOT_TOKEN }} > .env
    docker-compose up -d
```

## Troubleshooting

### Частые проблемы

#### 1. Бот не отвечает
```bash
# Проверка логов
docker logs yaedumerchbot

# Проверка переменных окружения
docker exec yaedumerchbot env | grep BOT
```

#### 2. Ошибки доступа к данным
```bash
# Проверка прав на volumes
docker exec yaedumerchbot ls -la /app/data

# Восстановление прав
docker exec yaedumerchbot chown -R 1000:1000 /app/data
```

#### 3. Высокое потребление памяти
```bash
# Анализ использования памяти
docker stats yaedumerchbot

# Ограничение ресурсов
docker update --memory=512m yaedumerchbot
```

### Отладка
```dockerfile
# Dockerfile.debug
FROM python:3.11-slim

# Установка отладочных инструментов
RUN apt-get update && apt-get install -y \
    vim \
    htop \
    procps \
    && rm -rf /var/lib/apt/lists/*

# ... остальной код
```

## Масштабирование

### Горизонтальное масштабирование
```yaml
# docker-compose.scale.yml
services:
  yaedumerchbot:
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
```

**Ограничения:**
- Long polling не поддерживает несколько экземпляров
- Требуется миграция на webhook режим
- Необходима внешняя база данных

### Вертикальное масштабирование
```yaml
services:
  yaedumerchbot:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '2.0'
        reservations:
          memory: 512M
          cpus: '1.0'
```
