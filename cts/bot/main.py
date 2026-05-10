# bot/main.py
import logging
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
)
from . import config
from .state_manager import StateManager
from .handlers import cmd_start, cmd_cancel, handle_callback, handle_message
from .admin_handlers import cmd_admin, cmd_sync

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=getattr(logging, config.LOG_LEVEL),
)
logger = logging.getLogger(__name__)


def main():
    if not config.BOT_TOKEN:
        raise ValueError("BOT_TOKEN не задан в .env")
    if not config.MANAGERS_GROUP_ID:
        logger.warning("MANAGERS_GROUP_ID не задан — заявки в группу не отправятся")
    if not config.ADMIN_IDS:
        logger.warning("ADMIN_IDS не заданы — admin-команды недоступны")
    else:
        logger.info(f"Администраторы: {config.ADMIN_IDS}")

    app = Application.builder().token(config.BOT_TOKEN).build()
    app.bot_data["sm"] = StateManager()

    # Обычные команды
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("cancel", cmd_cancel))

    # Admin-команды
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CommandHandler("sync", cmd_sync))

    # Inline кнопки
    app.add_handler(CallbackQueryHandler(handle_callback))

    # Текстовые сообщения
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Бот запущен. Ctrl+C для остановки.")
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()