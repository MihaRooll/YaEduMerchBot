# Переменные окружения для GitHub Actions

Этот файл содержит документацию по переменным окружения, используемым в workflow файлах.

## Общие переменные:

### Docker настройки:
- `DOCKER_REGISTRY`: docker.io
- `IMAGE_NAME`: yaedumerchbot

### Настройки проекта:
- `PROJECT_NAME`: YaEduMerchBot
- `PYTHON_VERSION`: "3.11"

### Настройки деплоя:
- `COMPOSE_PROJECT_NAME`: yaedumerchbot
- `COMPOSE_FILE`: compose.yml
- `COMPOSE_PREVIEW_FILE`: compose.preview.yml

### Настройки логирования:
- `LOG_RETENTION_DAYS`: 7
- `LOG_TAIL_LINES`: 200

## Использование в workflow:

Эти переменные можно использовать в файлах workflow следующим образом:

```yaml
env:
  IMAGE_NAME: yaedumerchbot
  PROJECT_NAME: YaEduMerchBot
```
