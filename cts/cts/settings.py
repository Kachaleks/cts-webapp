"""
Django settings for cts project.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ══════════════════════════════════════
# Безопасность
# ══════════════════════════════════════
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-dev-only-change-in-production')
DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# ══════════════════════════════════════
# Приложения
# ══════════════════════════════════════
INSTALLED_APPS = [
    "main",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "cts.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "cts.wsgi.application"

# ══════════════════════════════════════
# База данных
# Локально: db.sqlite3 рядом с manage.py
# В Docker: /app/db/db.sqlite3 (volume)
# ══════════════════════════════════════
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.getenv("DJANGO_DB_PATH", BASE_DIR / "db.sqlite3"),
    }
}
# ══════════════════════════════════════
# Валидация паролей
# ══════════════════════════════════════
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ══════════════════════════════════════
# Интернационализация
# ══════════════════════════════════════
LANGUAGE_CODE = "ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True

# ══════════════════════════════════════
# Статика
# ══════════════════════════════════════
STATIC_URL = "/static/"

STATICFILES_DIRS = [
    BASE_DIR / "main/static/",
]

# Куда collectstatic складывает файлы (для Docker/продакшена)
STATIC_ROOT = BASE_DIR / "staticfiles"

# ══════════════════════════════════════
# Медиафайлы (загружаемые через админку)
# upload_to='camera_images/' → итого: media/camera_images/файл.jpg
# ══════════════════════════════════════
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ══════════════════════════════════════
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"