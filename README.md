# B2B Lead Management API (CRM-ядро)

REST API-сервис для управления заявками (лидами) в B2B-сегменте. Система позволяет регистрировать пользователей, распределять заявки между менеджерами, отслеживать статусы и формировать отчёты. Предусмотрена админ-панель.

## Стек технологий

| Слой | Технология |
|------|-----------|
| Язык | Python 3.11+ |
| Фреймворк | FastAPI |
| ORM | SQLAlchemy 2.0 (async) |
| БД | PostgreSQL 15+ |
| Миграции | Alembic |
| Валидация | Pydantic v2 |
| Авторизация | JWT (access + refresh токены) |
| Админка | SQLAdmin |
| Контейнеризация | Docker + docker-compose |
| Тесты | pytest + httpx |

## Быстрый старт

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd <project-directory>
```

### 2. Настройка переменных окружения

Скопируйте файл `.env.example` в `.env`:

```bash
cp .env.example .env
```

При необходимости измените значения в `.env`.

### 3. Запуск через Docker Compose

```bash
docker-compose up --build
```

После запуска:
- **API** доступен по адресу: http://localhost:8000
- **Swagger документация**: http://localhost:8000/docs
- **Админ-панель**: http://localhost:8000/admin

## Учётные данные для тестирования

После первого запуска автоматически создаются следующие пользователи:

| Роль | Email | Пароль |
|------|-------|--------|
| Admin | `admin@crm.local` | `admin123` |
| Manager 1 | `manager1@crm.local` | `manager123` |
| Manager 2 | `manager2@crm.local` | `manager123` |

## Примеры запросов

### Регистрация нового пользователя (только admin)

```bash
# Сначала нужно получить токен админа
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@crm.local", "password": "admin123"}'

# Затем создать пользователя (используя полученный access_token)
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "email": "newmanager@crm.local",
    "password": "password123",
    "role": "manager"
  }'
```

### Создание заявки

```bash
curl -X POST "http://localhost:8000/leads" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "title": "Новый проект",
    "description": "Описание проекта",
    "company_name": "ООО Ромашка",
    "contact_email": "contact@romashka.ru"
  }'
```

### Получение списка заявок с фильтрацией

```bash
# Все заявки (admin)
curl -X GET "http://localhost:8000/leads?page=1&per_page=20" \
  -H "Authorization: Bearer <access_token>"

# Только заявки со статусом "in_progress"
curl -X GET "http://localhost:8000/leads?status=in_progress" \
  -H "Authorization: Bearer <access_token>"

# Заявки конкретного менеджера (admin)
curl -X GET "http://localhost:8000/leads?manager_id=<uuid>" \
  -H "Authorization: Bearer <access_token>"
```

### Обновление статуса заявки (с проверкой машины состояний)

```bash
# Разрешённый переход: new → in_progress
curl -X PATCH "http://localhost:8000/leads/<lead_id>" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"status": "in_progress"}'

# Запрещённый переход: new → won (вернёт 400)
curl -X PATCH "http://localhost:8000/leads/<lead_id>" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"status": "won"}'
```

### Отчёты (только admin)

```bash
# Конверсия по статусам
curl -X GET "http://localhost:8000/reports/conversion" \
  -H "Authorization: Bearer <access_token>"

# Статистика по менеджерам
curl -X GET "http://localhost:8000/reports/managers" \
  -H "Authorization: Bearer <access_token>"

# Динамика новых лидов
curl -X GET "http://localhost:8000/reports/dynamics?period=daily&days=30" \
  -H "Authorization: Bearer <access_token>"
```

## Машина состояний (статусы заявок)

Разрешённые переходы:

```
new → in_progress
in_progress → negotiation, lost
negotiation → won, lost
```

Статусы `won` и `lost` являются терминальными — переходы из них запрещены.

При попытке недопустимого перехода API вернёт ошибку `400 Bad Request`.

## Структура проекта

```
.
├── alembic/                 # Миграции БД
├── app/
│   ├── middleware/          # Middleware (авторизация)
│   ├── models/              # SQLAlchemy модели
│   ├── repositories/        # Repository слой для работы с БД
│   ├── routers/             # API роутеры
│   ├── schemas/             # Pydantic схемы
│   ├── services/            # Бизнес-логика
│   ├── admin.py             # SQLAdmin конфигурация
│   ├── config.py            # Настройки приложения
│   ├── database.py          # Подключение к БД
│   └── main.py              # Точка входа
├── tests/                   # Тесты
├── docker-compose.yml       # Docker Compose конфигурация
├── Dockerfile               # Docker образ приложения
├── requirements.txt         # Python зависимости
├── seed.py                  # Скрипт для создания тестовых данных
└── README.md                # Документация
```

## Запуск тестов

```bash
# Запустить все тесты
pytest

# Запустить с покрытием
pytest --cov=app
```

## Админ-панель

Админ-панель SQLAdmin доступна по адресу `/admin` и предоставляет:

- Просмотр и редактирование пользователей
- Управление заявками (лидами)
- Просмотр истории изменения статусов
- Фильтрация по статусу, менеджеру, дате
- Экспорт данных в CSV

## Обработка ошибок

Все ошибки возвращаются в едином формате:

```json
{
  "detail": "Описание ошибки"
}
```

Коды ответов:
- `200` — успешное выполнение
- `201` — ресурс создан
- `204` — ресурс удалён
- `400` — неверный запрос (например, недопустимый переход статуса)
- `401` — неавторизован
- `403` — доступ запрещён (недостаточно прав)
- `404` — ресурс не найден
- `500` — внутренняя ошибка сервера
