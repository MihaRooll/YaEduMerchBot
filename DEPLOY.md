# Руководство по деплою YaEduMerchBot

## Обзор

YaEduMerchBot использует автоматизированную систему CI/CD на основе GitHub Actions и Docker для деплоя.

## Архитектура деплоя

### Основные компоненты:
- **GitHub Actions** - автоматизация CI/CD
- **Docker** - контейнеризация приложения
- **Docker Compose** - оркестрация контейнеров
- **Self-hosted runner** - выполнение деплоя на собственном сервере

## Настройка секретов

В настройках репозитория GitHub необходимо добавить следующие секреты:

### Обязательные секреты:
```
BOT_TOKEN=your_telegram_bot_token_here
DOCKERHUB_USERNAME=your_dockerhub_username
DOCKERHUB_TOKEN=your_dockerhub_token
```

### Дополнительные секреты:
```
DATABASE_URL=sqlite:///bot.db
ADMIN_IDS=123456789,987654321
PAYMENT_TOKEN=your_payment_provider_token
```

## Workflow файлы

### 1. deploy.yml
Основной деплой при пуше в main ветку и при создании Pull Request:
- Собирает Docker образ
- Публикует в Docker Hub
- Деплоит на production сервер
- Собирает и публикует логи

### 2. pr-preview.yml
Деплой preview версии для Pull Request:
- Собирает образ для PR
- Деплоит preview версию
- Добавляет комментарий с логами в PR

### 3. pr-preview-cleanup.yml
Очистка preview версии при закрытии PR:
- Останавливает preview контейнеры
- Удаляет временные образы
- Очищает ресурсы

## Структура Docker

### Dockerfile
- Базовый образ: Python 3.11-slim
- Установка зависимостей из requirements.txt
- Создание пользователя app для безопасности
- Экспорт порта 8443 для webhook

### compose.yml (Production)
```yaml
services:
  yaedumerchbot:
    image: ${DOCKERHUB_USERNAME}/yaedumerchbot:latest
    container_name: yaedumerchbot
    restart: unless-stopped
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - DATABASE_URL=${DATABASE_URL}
      - ADMIN_IDS=${ADMIN_IDS}
      - PAYMENT_TOKEN=${PAYMENT_TOKEN}
    volumes:
      - bot_data:/app/data
      - ./logs:/app/logs
    ports:
      - "8443:8443"
```

### compose.preview.yml (Preview)
Аналогично production, но с:
- Отдельной базой данных для каждого PR
- DEBUG режимом
- Уникальными именами контейнеров

## Self-hosted Runner

Требования к серверу:
- Windows с PowerShell
- Docker Desktop
- GitHub Actions Runner
- Метки: `[self-hosted, Windows, X64, yaedumerchbot]`

### Установка runner:
1. Перейти в Settings → Actions → Runners
2. Нажать "New self-hosted runner"
3. Выбрать Windows x64
4. Следовать инструкциям по установке
5. Добавить метку `yaedumerchbot`

## Мониторинг и логи

### Автоматический сбор логов:
- Логи собираются после каждого деплоя
- Маскируются токены и секреты
- Сохраняются как артефакты (7 дней)
- Добавляются в комментарии к коммитам/PR

### Просмотр логов:
```bash
# Production логи
docker compose -f compose.yml -p yaedumerchbot logs -f

# Preview логи
docker compose -f compose.preview.yml -p yaedumerchbot_pr_<PR_NUM> logs -f
```

## Troubleshooting

### Проблемы с деплоем:
1. Проверить статус runner в GitHub
2. Проверить доступность Docker на сервере
3. Проверить корректность секретов
4. Просмотреть логи в GitHub Actions

### Проблемы с ботом:
1. Проверить токен бота
2. Проверить доступность Telegram API
3. Проверить логи контейнера
4. Проверить переменные окружения

### Команды для отладки:
```bash
# Проверить статус контейнеров
docker ps

# Проверить логи
docker logs yaedumerchbot

# Перезапустить бота
docker compose -f compose.yml -p yaedumerchbot restart

# Полная пересборка
docker compose -f compose.yml -p yaedumerchbot down
docker compose -f compose.yml -p yaedumerchbot up -d --build
```

## Безопасность

### Меры безопасности:
- Все секреты хранятся в GitHub Secrets
- Токены маскируются в логах
- Контейнер запускается от непривилегированного пользователя
- Используется минимальный базовый образ

### Рекомендации:
- Регулярно обновлять зависимости
- Мониторить логи на предмет подозрительной активности
- Использовать сильные пароли для всех сервисов
- Ограничить доступ к серверу деплоя

## Обновление

### Автоматическое обновление:
- При пуше в main ветку автоматически запускается деплой
- Образ пересобирается и обновляется
- Контейнер перезапускается с новой версией

### Ручное обновление:
1. Запустить workflow вручную через GitHub Actions
2. Или выполнить команды на сервере:
```bash
docker pull your_username/yaedumerchbot:latest
docker compose -f compose.yml -p yaedumerchbot up -d
```
