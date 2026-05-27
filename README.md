# Price Monitor v2

Сервис мониторинга цен: парсит товары с Citilink, сохраняет историю цен в PostgreSQL и отправляет уведомления в Telegram при снижении цены или достижении целевой цены.

## Возможности

- Добавление товаров через Telegram: `/add <url>`
- Просмотр списка товаров: `/list`
- Отключение товара: `/remove <id>`
- Установка целевой цены: `/target <id> <цена>`
- Ручная проверка цен: `/check`
- Автоматическая проверка по интервалу из `.env`
- История цен в PostgreSQL

## Установка

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

Создай `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

## Запуск

Запустить Telegram-бота:

```bash
python -m app.bot
```

Запустить мониторинг отдельным процессом:

```bash
python -m app.monitor
```

## База данных

Таблицы создаются автоматически при запуске. Также можно выполнить `schema.sql` вручную.
