# bot/config.py
"""
Конфигурация бота — все настройки берутся из .env
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ===== TELEGRAM =====
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# ID группы менеджеров (отрицательное число, например -1001234567890)
# Чтобы узнать ID: добавь бота в группу и напиши /get_id
MANAGERS_GROUP_ID = int(os.getenv("MANAGERS_GROUP_ID", "0"))

# ===== БАЗА ДАННЫХ =====
# Путь к Django SQLite — укажи абсолютный путь до db.sqlite3
DJANGO_DB_PATH = os.getenv("DJANGO_DB_PATH", "../cts/db.sqlite3")

# ===== EMAIL =====
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "true").lower() == "true"
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USER)
EMAIL_TO = os.getenv("EMAIL_TO", "")  # куда приходят заявки

# ===== ЛОГИРОВАНИЕ =====
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")