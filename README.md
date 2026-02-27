# 📷 Цифровые Телесистемы — Калькулятор видеонаблюдения

Сайт-визитка компании по установке систем видеонаблюдения с онлайн-калькулятором подбора камер.

## 🛠 Стек технологий

- **Backend:** Python 3, Django
- **Frontend:** HTML, CSS, Vanilla JavaScript (AJAX-фильтрация)
- **БД:** SQLite (dev) / легко переключается на PostgreSQL
- **Медиа:** Django ImageField, Pillow

## 📁 Структура проекта

```
cts/
├── manage.py
├── db.sqlite3
├── cts/                    # Настройки Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── main/                   # Основное приложение
    ├── models.py           # Модели Camera и CableSettings
    ├── views.py            # Единственный view: calculator()
    ├── urls.py
    ├── admin.py
    ├── migrations/
    ├── static/
    │   ├── js/main.js      # Карусель проектов
    │   └── main/
    │       ├── css/style.css
    │       └── img/        # Статичные изображения
    └── templates/
        └── main/
            ├── index.html      # Базовый шаблон
            └── calculator.html # Дочерний шаблон (блоки фильтров)
```

## ⚙️ Установка и запуск

```bash
# 1. Клонировать репозиторий
git clone <repo-url>
cd cts

# 2. Создать виртуальное окружение
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Установить зависимости
pip install django pillow

# 4. Применить миграции
python manage.py migrate

# 5. Создать суперпользователя
python manage.py createsuperuser

# 6. Запустить сервер
python manage.py runserver
```

Сайт доступен по адресу: http://127.0.0.1:8000  
Админка: http://127.0.0.1:8000/admin

## 🗃 Модели

### Camera
| Поле | Тип | Описание |
|------|-----|----------|
| name | CharField | Название камеры |
| price | IntegerField | Цена (руб) |
| picture | ImageField | Фото (загружается в `camera_images/`) |
| resolution | IntegerField | Разрешение (Мп) |
| type | CharField | Тип (купольная, цилиндрическая и др.) |
| night_vision_technology | CharField | Технология ночного видения |
| connection_type | CharField | Тип подключения |
| lens | CharField | Тип объектива |
| has_zoom | BooleanField | Наличие зума |
| has_micro | BooleanField | Наличие микрофона |
| has_dynamic | BooleanField | Наличие динамика |
| has_people_analytics | BooleanField | Аналитика по людям |
| has_cars_analytics | BooleanField | Аналитика по ТС |
| has_special_cars_analytics | BooleanField | Аналитика по спец. ТС |

### CableSettings
Хранит стоимость кабеля за метр. Всегда активна только одна запись (`is_active=True`).

## 🔌 API (AJAX)

`GET /?<фильтры>` с заголовком `X-Requested-With: XMLHttpRequest`

**Параметры фильтрации:**

| Параметр | Тип | Пример |
|----------|-----|--------|
| resolution | int | `?resolution=4` |
| type | string | `?type=Купольная` |
| night_vision_technology | string | `?night_vision_technology=Color` |
| connection_types | string | `?connection_types=Провод` |
| lens | string (multiple) | `?lens=2.8&lens=4` |
| has_zoom | bool string | `?has_zoom=true` |
| has_micro | — | `?has_micro=true` |
| has_dynamic | — | `?has_dynamic=true` |
| has_people_analytics | — | `?has_people_analytics=true` |
| has_cars_analytics | — | `?has_cars_analytics=true` |
| has_special_cars_analytics | — | `?has_special_cars_analytics=true` |

**Пример ответа:**
```json
{
  "cameras": [
    {
      "id": 1,
      "name": "HiWatch DS-I425B",
      "type": "Купольная",
      "resolution": 4,
      "connection_type": "Провод",
      "price": 4500,
      "picture": "/media/camera_images/hiwatch.png",
      "has_micro": false,
      "has_zoom": false,
      "has_dynamic": false
    }
  ],
  "cable_price": 125
}
```

## 🔧 Настройки для продакшена

В `settings.py` перед деплоем:
```python
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.ru']
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        ...
    }
}
MEDIA_ROOT = '/var/www/media/'
MEDIA_URL = '/media/'
STATIC_ROOT = '/var/www/static/'
```