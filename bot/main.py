# bot/main.py
"""
Точка входа бота
"""
import logging
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
)
import config as config
from state_manager import StateManager
from handlers import (
    cmd_start, cmd_cancel,
    handle_callback, handle_message,
)

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

    app = Application.builder().token(config.BOT_TOKEN).build()

    # Шаримся StateManager через bot_data
    app.bot_data["sm"] = StateManager()

    # Команды
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("cancel", cmd_cancel))

    # Inline кнопки
    app.add_handler(CallbackQueryHandler(handle_callback))

    # Текстовые сообщения
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Бот запущен. Ctrl+C для остановки.")
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()