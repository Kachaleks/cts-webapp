# bot/notifier.py
"""
Отправка уведомлений: в Telegram группу менеджеров и на email
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional

import bot.config as config
from models import BotOrder

logger = logging.getLogger(__name__)


def format_order_for_managers(order: BotOrder, cable_price_per_meter: int,
                               source: str = "бот") -> str:
    """Форматирует заявку в красивое сообщение для менеджеров"""
    totals = order.calculate_total(cable_price_per_meter)
    now = datetime.now().strftime("%d.%m.%Y %H:%M")

    lines = [
        f"🔔 <b>НОВАЯ ЗАЯВКА</b> [{source.upper()}]",
        f"🕐 {now}",
        "",
        "👤 <b>Клиент:</b>",
        f"  Имя: {order.client_name or '—'}",
        f"  Телефон: {order.client_phone or '—'}",
        "",
        "📦 <b>Состав заказа:</b>",
    ]

    for item in order.cart:
        cable_info = f", кабель {item.cable_meters} м × {item.quantity} = {item.cable_meters * item.quantity} м" \
                     if item.cable_meters > 0 else ""
        lines.append(
            f"  • {item.camera_name}\n"
            f"    {item.quantity} шт. × {item.camera_price:,} ₽ = {item.cameras_total:,} ₽{cable_info}"
        )

    lines += [
        "",
        "💰 <b>Итого:</b>",
        f"  Камеры: {totals['cameras_total']:,} ₽",
    ]

    if totals["cable_meters"] > 0:
        lines += [
            f"  Кабель ({totals['cable_meters']} м × {cable_price_per_meter} ₽): {totals['cable_total']:,} ₽",
            f"  Монтаж кабеля: {totals['installation_total']:,} ₽",
        ]

    lines += [
        f"",
        f"  <b>ИТОГО: {totals['grand_total']:,} ₽</b>",
    ]

    # Фильтры (что искал клиент)
    active_filters = order.get_active_filters()
    if active_filters:
        lines += ["", "🔍 <b>Параметры подбора:</b>"]
        labels = {
            "type": "Тип камеры",
            "connection_type": "Подключение",
            "resolution": "Разрешение (Мп)",
            "night_vision_technology": "Ночное видение",
            "has_people_analytics": "Аналитика: люди",
            "has_cars_analytics": "Аналитика: ТС",
            "has_micro": "Микрофон",
            "has_zoom": "Зум",
        }
        for k, v in active_filters.items():
            label = labels.get(k, k)
            lines.append(f"  {label}: {v}")

    return "\n".join(lines)


def format_order_plain_text(order: BotOrder, cable_price_per_meter: int,
                             source: str = "бот") -> str:
    """Форматирует заявку в plain text для email"""
    totals = order.calculate_total(cable_price_per_meter)
    now = datetime.now().strftime("%d.%m.%Y %H:%M")

    lines = [
        f"НОВАЯ ЗАЯВКА [{source.upper()}] — {now}",
        "=" * 50,
        "",
        "КЛИЕНТ:",
        f"  Имя: {order.client_name or '—'}",
        f"  Телефон: {order.client_phone or '—'}",
        "",
        "СОСТАВ ЗАКАЗА:",
    ]

    for item in order.cart:
        lines.append(f"  {item.camera_name} — {item.quantity} шт. × {item.camera_price:,} руб. = {item.cameras_total:,} руб.")
        if item.cable_meters > 0:
            lines.append(f"    Кабель: {item.cable_meters} м × {item.quantity} = {item.cable_meters * item.quantity} м")

    lines += [
        "",
        "ИТОГО:",
        f"  Камеры: {totals['cameras_total']:,} руб.",
    ]

    if totals["cable_meters"] > 0:
        lines += [
            f"  Кабель ({totals['cable_meters']} м × {cable_price_per_meter} руб/м): {totals['cable_total']:,} руб.",
            f"  Монтаж кабеля: {totals['installation_total']:,} руб.",
        ]

    lines += [
        "",
        f"  ИТОГО К ОПЛАТЕ: {totals['grand_total']:,} руб.",
    ]

    return "\n".join(lines)


async def send_to_telegram_group(bot, order: BotOrder, cable_price_per_meter: int,
                                  source: str = "бот"):
    """Отправляет заявку в группу менеджеров через бота"""
    if not config.MANAGERS_GROUP_ID:
        logger.warning("MANAGERS_GROUP_ID не задан, пропускаем отправку в группу")
        return

    text = format_order_for_managers(order, cable_price_per_meter, source)
    try:
        await bot.send_message(
            chat_id=config.MANAGERS_GROUP_ID,
            text=text,
            parse_mode="HTML",
        )
        logger.info(f"Заявка отправлена в группу {config.MANAGERS_GROUP_ID}")
    except Exception as e:
        logger.error(f"Ошибка отправки в группу: {e}", exc_info=True)


def send_email(order: BotOrder, cable_price_per_meter: int, source: str = "бот"):
    """Отправляет заявку на email"""
    if not config.EMAIL_ENABLED:
        return
    if not config.SMTP_USER or not config.EMAIL_TO:
        logger.warning("Email не настроен, пропускаем отправку")
        return

    try:
        body = format_order_plain_text(order, cable_price_per_meter, source)
        client_name = order.client_name or "Клиент"

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Новая заявка от {client_name} — Цифровые Телесистемы"
        msg["From"] = config.EMAIL_FROM
        msg["To"] = config.EMAIL_TO
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
            server.starttls()
            server.login(config.SMTP_USER, config.SMTP_PASSWORD)
            server.sendmail(config.EMAIL_FROM, config.EMAIL_TO, msg.as_string())

        logger.info(f"Email отправлен на {config.EMAIL_TO}")
    except Exception as e:
        logger.error(f"Ошибка отправки email: {e}", exc_info=True)