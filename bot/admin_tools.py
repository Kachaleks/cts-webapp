# bot/admin_tools.py
"""
Утилиты для admin-команд: декоратор проверки прав.
"""
import logging
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

import config

logger = logging.getLogger(__name__)


def admin_only(func):
    """
    Декоратор: пропускает только пользователей из config.ADMIN_IDS.
    Остальным отвечает 'нет доступа' и не выполняет команду.
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id

        if user_id not in config.ADMIN_IDS:
            logger.warning(f"Попытка доступа к admin-команде от user_id={user_id}")
            await update.message.reply_text("⛔ У вас нет доступа к этой команде.")
            return

        return await func(update, context)
    return wrapper


def is_admin(user_id: int) -> bool:
    """Проверка является ли пользователь администратором."""
    return user_id in config.ADMIN_IDS