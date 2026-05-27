# Price Monitor Bot

Telegram-бот для мониторинга цен товаров в интернет-магазине Citilink.

Проект позволяет добавлять товары для отслеживания, сохраняет историю цен в PostgreSQL и отправляет уведомления в Telegram при снижении цены или достижении целевой цены.

## Возможности

- Добавление товаров по ссылке
- Получение актуальной цены товара
- Сохранение истории цен в PostgreSQL
- Telegram-уведомления при снижении цены
- Поддержка целевой цены
- Просмотр списка отслеживаемых товаров
- Ручная проверка цен через Telegram
- Кнопочный интерфейс Telegram-бота
- Автоматическая проверка цен по расписанию

## Стек технологий

- Python
- aiogram
- Playwright
- PostgreSQL
- psycopg2
- python-dotenv

## Структура проекта

```text
price-monitor/
├── app/
│   ├── bot.py          # Telegram-бот
│   ├── config.py       # Настройки проекта
│   ├── database.py     # Работа с PostgreSQL
│   ├── monitor.py      # Автоматический мониторинг цен
│   ├── notifier.py     # Telegram-уведомления
│   └── scraper.py      # Парсер товаров
├── .env.example        # Пример переменных окружения
├── .gitignore
├── README.md
├── requirements.txt
└── schema.sql

## Как работает проект

Пользователь добавляет ссылку на товар через Telegram-бота.
Бот получает название и цену товара с помощью Playwright.
Информация о товаре сохраняется в PostgreSQL.
Мониторинг периодически проверяет актуальную цену.
Если цена снизилась или стала ниже целевой цены, бот отправляет уведомление.
Установка

Склонируйте репозиторий:

git clone https://github.com/USERNAME/price-monitor.git
cd price-monitor

Создайте виртуальное окружение:

python3 -m venv .venv
source .venv/bin/activate

Установите зависимости:

pip install -r requirements.txt

Установите браузер для Playwright:

playwright install chromium
Настройка окружения

Создайте файл .env на основе .env.example:

cp .env.example .env

Пример .env:

DB_NAME=dns_monitor
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

BOT_TOKEN=your_telegram_bot_token
MY_CHAT_ID=your_telegram_chat_id

CHECK_INTERVAL_SECONDS=3600
HEADLESS=true
Настройка базы данных

Создайте базу данных PostgreSQL:

createdb dns_monitor

Или через psql:

CREATE DATABASE dns_monitor;

Таблицы создаются автоматически при запуске приложения. Также структуру можно посмотреть в файле schema.sql.

Запуск

Запуск Telegram-бота:

python3 -m app.bot

Запуск мониторинга цен:

python3 -m app.monitor

Рекомендуется запускать бота и мониторинг в двух разных терминалах.

Команды Telegram-бота
/start — открыть меню
/list — показать отслеживаемые товары
/add <url> — добавить товар
/add <url> <target_price> — добавить товар с целевой ценой
/remove <id> — отключить товар
/target <id> <price> — установить целевую цену
/check — проверить цены вручную
/help — помощь
Кнопочный интерфейс

В боте доступны кнопки:

➕ Добавить товар
📦 Мои товары
🔍 Проверить цены
❓ Помощь

Это позволяет пользоваться системой без ручного ввода команд.

Пример уведомления
🔥 Найдена скидка!

Товар: Apple iPhone 16 256GB
Цена упала: 84 990 ₽ → 77 490 ₽
Экономия: 7 500 ₽

Открыть товар:
https://www.citilink.ru/product/...
Планы по развитию
Веб-интерфейс на React
График истории цен
Docker Compose для быстрого запуска
Поддержка нескольких магазинов
Авторизация пользователей
Фильтрация товаров по категориям
Экспорт истории цен в CSV

Автор
Проект разработан как pet-проект для практики Python, PostgreSQL, Telegram Bot API и автоматизации мониторинга цен.