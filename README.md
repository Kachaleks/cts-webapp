# 📷 Цифровые Телесистемы — Калькулятор видеонаблюдения

Сайт-визитка компании по установке систем видеонаблюдения с онлайн-калькулятором подбора камер и Telegram-ботом для приёма заявок.

## 🛠 Стек технологий

- **Backend:** Python 3.11, Django 4.2
- **Frontend:** HTML, CSS, Vanilla JavaScript (AJAX-фильтрация)
- **БД:** SQLite (общая для сайта и бота)
- **Бот:** python-telegram-bot 21
- **Уведомления:** Telegram группа менеджеров + Email (SMTP)
- **Деплой:** Docker + docker-compose

## 📁 Структура проекта

```
project/
├── docker-compose.yml
├── Dockerfile              # Общий для Django и бота
├── requirements.txt        # Общие зависимости
├── .env                    # Секреты (не в git)
├── .env.example            # Шаблон .env
├── .gitignore
│
├── cts/                    # Django приложение
│   ├── manage.py
│   ├── cts/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   └── main/
│       ├── models.py       # Camera, CableSettings
│       ├── views.py        # calculator(), send_order()
│       ├── urls.py
│       ├── admin.py
│       ├── migrations/
│       ├── static/
│       │   ├── js/main.js
│       │   └── main/
│       │       ├── css/style.css
│       │       └── img/
│       └── templates/
│           └── main/
│               ├── index.html
│               └── calculator.html
│
└── bot/                    # Telegram бот
    ├── main.py             # Точка входа
    ├── handlers.py         # Весь флоу диалога
    ├── db.py               # Чтение камер из SQLite
    ├── models.py           # BotOrder, CartItem
    ├── state_manager.py    # Состояния диалога
    ├── notifier.py         # Отправка в Telegram и email
    └── config.py           # Конфигурация из .env
```

## 🚀 Быстрый старт (Docker)

```bash
# 1. Клонировать репозиторий
git clone <repo-url>
cd project

# 2. Заполнить .env
cp .env.example .env
# отредактировать .env — минимум BOT_TOKEN и MANAGERS_GROUP_ID

# 3. Запустить
docker-compose up --build
```

Сайт: http://localhost:8000
Админка: http://localhost:8000/admin

**Создать суперпользователя (один раз):**
```bash
docker-compose exec django sh -c "cd /app/cts && python manage.py createsuperuser"
```

**Полезные команды:**
```bash
# Логи всех сервисов
docker-compose logs -f

# Логи отдельно
docker-compose logs -f django
docker-compose logs -f bot

# Остановить
docker-compose down

# Пересоздать БД с нуля
docker-compose down -v
docker-compose up --build
```

## ⚙️ Локальный запуск (без Docker)

```bash
# Зависимости
pip install -r requirements.txt

# Django
cd cts
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

# Бот (отдельный терминал)
cd bot
python main.py
```

## 🔑 Настройка .env

| Переменная | Обязательная | Описание |
|------------|:---:|----------|
| `BOT_TOKEN` | ✅ | Токен от @BotFather |
| `MANAGERS_GROUP_ID` | ✅ | ID группы менеджеров (отрицательное число) |
| `DJANGO_SECRET_KEY` | — | Секретный ключ Django (для продакшена) |
| `EMAIL_ENABLED` | — | Включить отправку email (true/false) |
| `SMTP_USER` | — | Email отправителя |
| `SMTP_PASSWORD` | — | App Password (не обычный пароль) |
| `EMAIL_TO` | — | Email куда приходят заявки |

**Как узнать MANAGERS_GROUP_ID:** добавь бота в группу, напиши сообщение, открой `https://api.telegram.org/bot<TOKEN>/getUpdates?offset=-1` — найди `"chat":{"id":-100xxxxxxxxx}`.

## 🤖 Бот — сценарий работы

```
/start
  → Тип камеры
  → Тип подключения
  → Разрешение
  → Ночное видение
  → Доп. опции (микрофон, зум, аналитика)
  → Список подходящих камер из БД
  → Выбор камер + количество + метры кабеля
  → Корзина с итогами
  → Имя клиента
  → Телефон
  → Подтверждение → отправка в группу менеджеров + email
```

## 🗃 Модели

### Camera
| Поле | Тип | Описание |
|------|-----|----------|
| name | CharField | Название |
| price | IntegerField | Цена (руб) |
| picture | ImageField | Фото |
| resolution | IntegerField | Разрешение (Мп) |
| type | CharField | Тип (купольная и др.) |
| night_vision_technology | CharField | Технология ночного видения |
| connection_type | CharField | Тип подключения |
| lens | CharField | Объектив |
| has_zoom | BooleanField | Зум |
| has_micro | BooleanField | Микрофон |
| has_dynamic | BooleanField | Динамик |
| has_people_analytics | BooleanField | Аналитика: люди |
| has_cars_analytics | BooleanField | Аналитика: ТС |
| has_special_cars_analytics | BooleanField | Аналитика: спец. ТС |

### CableSettings
Стоимость кабеля за метр. Активна только одна запись (`is_active=True`).

## 🔌 API (AJAX)

`GET /?<фильтры>` с заголовком `X-Requested-With: XMLHttpRequest`

| Параметр | Пример |
|----------|--------|
| resolution | `?resolution=4` |
| type | `?type=Купольная` |
| night_vision_technology | `?night_vision_technology=Color` |
| connection_types | `?connection_types=Провод` |
| lens | `?lens=2.8&lens=4` |
| has_zoom | `?has_zoom=true` |
| has_micro | `?has_micro` |
| has_people_analytics | `?has_people_analytics` |

`POST /send-order/` — приём заявки с сайта, отправка в Telegram и email.