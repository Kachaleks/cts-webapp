# bot/notifier.py
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from . import config

logger = logging.getLogger(__name__)

LABELS = {
    "city":    "В черте города",
    "30km":    "До 30 км",
    "100km":   "30–100 км",
    "far":     "Более 100 км",
    "fullhd":  "Full HD (2 Мп)",
    "4k":      "4K (8 Мп)",
    "any":     "На ваш выбор",
    "outdoor": "На улице",
    "indoor":  "Внутри помещений",
    "both":    "И снаружи, и внутри",
    "7":       "7 дней",
    "14":      "14 дней",
    "30":      "30 дней",
    "60+":     "60+ дней",
    "1-2":     "1–2 камеры",
    "3-5":     "3–5 камер",
    "6-10":    "6–10 камер",
    "10+":     "Больше 10",
}


def _label(val):
    return LABELS.get(val, val or "—")


def _format_telegram(order) -> str:
    ts = order.completed_at.strftime("%d.%m.%Y %H:%M") if order.completed_at else "—"
    return (
        f"📥 <b>Новая заявка с бота</b>\n"
        f"🕐 {ts}\n\n"
        f"👤 Имя: <b>{order.client_name}</b>\n"
        f"📞 Телефон: <b>{order.client_phone}</b>\n\n"
        f"📍 Расположение: {_label(order.distance)}\n"
        f"📷 Камеры: {_label(order.quality)}\n"
        f"🏠 Установка: {_label(order.location)}\n"
        f"🔢 Количество: {_label(order.camera_count)}\n"
        f"💾 Хранение: {_label(order.storage)}\n"
    )


def _format_email(order) -> str:
    ts = order.completed_at.strftime("%d.%m.%Y %H:%M") if order.completed_at else "—"
    return (
        f"Новая заявка с бота — {ts}\n\n"
        f"Имя: {order.client_name}\n"
        f"Телефон: {order.client_phone}\n\n"
        f"Расположение: {_label(order.distance)}\n"
        f"Камеры: {_label(order.quality)}\n"
        f"Установка: {_label(order.location)}\n"
        f"Количество: {_label(order.camera_count)}\n"
        f"Хранение: {_label(order.storage)}\n"
    )


async def send_to_telegram_group(bot, order):
    if not config.MANAGERS_GROUP_ID:
        logger.warning("MANAGERS_GROUP_ID не задан, пропускаем")
        return
    try:
        await bot.send_message(
            chat_id=config.MANAGERS_GROUP_ID,
            text=_format_telegram(order),
            parse_mode="HTML",
        )
        logger.info("Заявка отправлена в Telegram группу")
    except Exception as e:
        logger.error(f"Ошибка отправки в Telegram: {e}")


def send_email(order):
    if not config.EMAIL_ENABLED:
        return
    if not config.SMTP_USER or not config.EMAIL_TO:
        logger.warning("Email не настроен, пропускаем")
        return
    try:
        msg = MIMEMultipart()
        msg["From"] = config.EMAIL_FROM
        msg["To"] = config.EMAIL_TO
        msg["Subject"] = f"Новая заявка — {order.client_name}"
        msg.attach(MIMEText(_format_email(order), "plain", "utf-8"))

        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
            server.starttls()
            server.login(config.SMTP_USER, config.SMTP_PASSWORD)
            server.send_message(msg)

        logger.info("Заявка отправлена на email")
    except Exception as e:
        logger.error(f"Ошибка отправки email: {e}")