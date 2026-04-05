# VPN Remna API

Backend API — middleware между Telegram Mini App, Telegram Bot и Remnawave панелью.

**Stack:** FastAPI · MySQL 8 · SQLAlchemy 2 (async) · Alembic · Docker

---

## Архитектура

```
Telegram Mini App  ──►  /api/v1/auth/telegram    (JWT)
                    ──►  /api/v1/users/me
                    ──►  /api/v1/subscriptions/*
                    ──►  /api/v1/wallet/*
                    ──►  /api/v1/referrals/*

YooKassa           ──►  /api/v1/webhooks/yookassa
Remnawave          ──►  /api/v1/webhooks/remnawave

Admin Panel        ──►  /api/v1/admin/*           (Admin JWT)
```

---

## Быстрый старт (Docker)

```bash
cp .env.example .env
# Заполни .env своими значениями

docker compose up -d
```

API будет доступен по `http://localhost:8000`.

Swagger UI (только при `DEBUG=true`): `http://localhost:8000/docs`

---

## Локальный запуск

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # заполни значения

# Применить миграции
alembic upgrade head

# Создать первого суперадмина
curl -X POST http://localhost:8000/api/v1/admin/register-first \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "YOUR_STRONG_PASSWORD"}'

uvicorn app.main:app --reload --port 8000
```

---

## Миграции (Alembic)

```bash
# Создать новую миграцию после изменения моделей
alembic revision --autogenerate -m "описание изменения"

# Применить все миграции
alembic upgrade head

# Откат последней миграции
alembic downgrade -1
```

---

## Переменные окружения

Все переменные описаны в `.env.example`. Обязательные:

| Переменная | Описание |
|---|---|
| `SECRET_KEY` | Случайная строка 32+ символов |
| `DB_*` | Параметры подключения к MySQL |
| `TELEGRAM_BOT_TOKEN` | Токен Telegram бота |
| `REMNAWAVE_URL` | URL Remnawave панели |
| `REMNAWAVE_API_KEY` | JWT API ключ Remnawave |
| `JWT_SECRET_KEY` | Секрет для подписи admin JWT |

---

## API эндпоинты

### Аутентификация
| Метод | Путь | Описание |
|---|---|---|
| POST | `/api/v1/auth/telegram` | Вход через Telegram WebApp initData |

### Пользователь
| Метод | Путь | Описание |
|---|---|---|
| GET | `/api/v1/users/me` | Профиль текущего пользователя |
| GET | `/api/v1/users/me/referral-link` | Реферальная ссылка |

### Подписки
| Метод | Путь | Описание |
|---|---|---|
| GET | `/api/v1/subscriptions/catalog` | Каталог продуктов и планов |
| GET | `/api/v1/subscriptions/my` | Мои подписки |
| POST | `/api/v1/subscriptions/purchase` | Купить подписку с баланса |
| POST | `/api/v1/subscriptions/trial` | Активировать пробный период |
| POST | `/api/v1/subscriptions/renew` | Продлить подписку |
| POST | `/api/v1/subscriptions/toggle-auto-renewal/{id}` | Вкл/выкл автопродление |

### Кошелёк
| Метод | Путь | Описание |
|---|---|---|
| GET | `/api/v1/wallet` | Баланс кошелька |
| GET | `/api/v1/wallet/transactions` | История транзакций |
| POST | `/api/v1/wallet/topup` | Пополнить через YooKassa |

### Рефералы
| Метод | Путь | Описание |
|---|---|---|
| GET | `/api/v1/referrals/stats` | Статистика реферальной программы |
| GET | `/api/v1/referrals/rewards` | История начислений |

### Вебхуки
| Метод | Путь | Описание |
|---|---|---|
| POST | `/api/v1/webhooks/yookassa` | YooKassa платёжные события |
| POST | `/api/v1/webhooks/remnawave` | Remnawave события подписок |

### Админка
| Метод | Путь | Описание |
|---|---|---|
| POST | `/api/v1/admin/login` | Вход в админ-панель |
| POST | `/api/v1/admin/register-first` | Создать первого суперадмина |
| GET | `/api/v1/admin/dashboard` | Дашборд |
| GET | `/api/v1/admin/users` | Список пользователей |
| POST | `/api/v1/admin/users/{id}/ban` | Забанить |
| POST | `/api/v1/admin/users/{id}/unban` | Разбанить |
| POST | `/api/v1/admin/wallet/adjust` | Ручная корректировка баланса |
| GET | `/api/v1/admin/remnawave/health` | Статус Remnawave |
| GET | `/api/v1/admin/audit-log` | Журнал действий |

---

## Подключение к Mini App

В `vpn-remna-miniapp` добавь `.env`:
```
VITE_API_URL=https://your-api-domain.com/api/v1
```

При запуске Mini App передавай `initData` из `window.Telegram.WebApp.initData` в заголовок:
```js
const response = await fetch(`${API_URL}/auth/telegram`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ init_data: window.Telegram.WebApp.initData }),
});
const { access_token } = await response.json();
// Сохрани access_token, используй в Authorization: Bearer <token>
```

---

## Remnawave Webhook настройка

В панели Remnawave укажи Webhook URL:
```
https://your-api-domain.com/api/v1/webhooks/remnawave
```

---

## YooKassa Webhook настройка

В личном кабинете YooKassa укажи Webhook URL:
```
https://your-api-domain.com/api/v1/webhooks/yookassa
```
Выбери события: `payment.succeeded`, `payment.canceled`
