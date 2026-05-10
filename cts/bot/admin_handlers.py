# bot/admin_handlers.py
"""
Команды доступные только администраторам.
Подключаются в main.py через CommandHandler.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from .admin_tools import admin_only
from .sheets_sync import SheetsManager

logger = logging.getLogger(__name__)


@admin_only
async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню администратора."""
    await update.message.reply_text(
        "🔧 <b>Панель администратора</b>\n\n"
        "Доступные команды:\n"
        "/sync — синхронизировать БД из Google Sheets\n",
        parse_mode="HTML",
    )


@admin_only
async def cmd_sync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Синхронизация БД из Google Sheets."""
    msg = await update.message.reply_text("⏳ Читаю данные из Google Sheets...")

    try:
        manager = SheetsManager()
        stats = manager.sync_all()

        await msg.edit_text(
            f"✅ <b>Синхронизация завершена</b>\n\n"
            f"📷 Камеры:\n"
            f"  • Обновлено: {stats['updated']}\n"
            f"  • Создано: {stats['created']}\n"
            f"  • Ошибок: {stats['errors']}",
            parse_mode="HTML",
        )

    except Exception as e:
        logger.error(f"Ошибка синхронизации: {e}")
        await msg.edit_text(
            f"❌ <b>Ошибка синхронизации</b>\n\n"
            f"<code>{str(e)}</code>",
            parse_mode="HTML",
        )