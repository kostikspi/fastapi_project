# URL Shortener

Сервис для сокращения длинных URL-адресов, построенный с использованием FastAPI, PostgreSQL и Redis.

## Установка и запуск

### Запуск с помощью Docker

1. Соберите и запустите контейнеры:
```bash
docker-compose up -d
```

2. Приложение будет доступно по адресу: http://localhost:8000
3. API документация: http://localhost:8000/docs
4. Интерфейс нагрузочного тестирования: http://localhost:8089

## API Endpoints

### Аутентификация
- `POST /api/v1/users/register` - Регистрация нового пользователя
- `POST /api/v1/users/login` - Вход в систему
- `POST /api/v1/users/token` - Получение токена доступа

### URL операции
- `POST /api/v1/links/shorten` - Создание короткого URL
- `GET /api/v1/links/{short_code}` - Перенаправление на оригинальный URL
- `DELETE /api/v1/links/{short_code}` - Удаление URL
- `PUT /api/v1/links/{short_code}` - Обновление URL
- `GET /api/v1/links/{short_code}/stats` - Получение статистики URL
- `GET /api/v1/links/search` - Поиск URL

## Тестирование

### Запуск тестов
```bash
pytest

docker-compose run test
```

### Запуск нагрузочного тестирования
```bash
docker-compose run loadtest
```

## Конфигурация

Настройки приложения хранятся в следующих местах:
- `docker-compose.yml` - настройки для Docker
- `src/application/core/config.py` - конфигурация приложения
