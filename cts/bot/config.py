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
MANAGERS_GROUP_ID = int(os.getenv("MANAGERS_GROUP_ID", "0"))

# ID администраторов бота (через запятую, например: 123456789,987654321)
ADMIN_IDS = [
    int(x.strip())
    for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
]

# ===== БАЗА ДАННЫХ =====
DJANGO_DB_PATH = os.getenv("DJANGO_DB_PATH", "../db.sqlite3")

# ===== EMAIL =====
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "true").lower() == "true"
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USER)
EMAIL_TO = os.getenv("EMAIL_TO", "")

# ===== ЛОГИРОВАНИЕ =====
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ===== GOOGLE SHEETS =====
# ID таблицы из URL: docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "")

# Путь к JSON файлу сервисного аккаунта
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "bot/credentials.json")