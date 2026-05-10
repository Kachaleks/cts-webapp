# bot/handlers.py
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from .state_manager import StateManager, State
from .notifier import send_to_telegram_group, send_email

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────

def kb(buttons: list, back: bool = True) -> InlineKeyboardMarkup:
    """Собирает клавиатуру. buttons — список списков InlineKeyboardButton."""
    rows = list(buttons)
    if back:
        rows.append([InlineKeyboardButton("⬅️ Назад", callback_data="nav:back")])
    return InlineKeyboardMarkup(rows)


# ─────────────────────────────────────────
# /start  /cancel
# ─────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sm: StateManager = context.bot_data["sm"]
    user_id = update.effective_user.id
    sm.reset(user_id)
    sm.set_state(user_id, State.START)

    await update.message.reply_text(
        "👋 <b>Добро пожаловать!</b>\n\n"
        "Я помогу подобрать систему видеонаблюдения и передам заявку менеджеру.\n\n"
        "Это займёт меньше минуты 👇",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🚀 Начать подбор", callback_data="nav:to_distance")
        ]])
    )


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sm: StateManager = context.bot_data["sm"]
    sm.reset(update.effective_user.id)
    await update.message.reply_text("❌ Отменено. /start — начать заново.")


# ─────────────────────────────────────────
# Шаг 1: Расстояние от города
# ─────────────────────────────────────────

async def show_distance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sm: StateManager = context.bot_data["sm"]
    query = update.callback_query
    sm.set_state(query.from_user.id, State.STEP_DISTANCE)

    await query.edit_message_text(
        "📍 <b>Шаг 1 из 5</b>\n\nГде находится объект?",
        parse_mode="HTML",
        reply_markup=kb([
            [InlineKeyboardButton("🏙 В черте города",       callback_data="distance:city")],
            [InlineKeyboardButton("🛣 До 30 км от города",   callback_data="distance:30km")],
            [InlineKeyboardButton("🛤 30–100 км",            callback_data="distance:100km")],
            [InlineKeyboardButton("🌍 Более 100 км",         callback_data="distance:far")],
        ], back=False)
    )


# ─────────────────────────────────────────
# Шаг 2: Качество камер
# ─────────────────────────────────────────

async def show_quality(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sm: StateManager = context.bot_data["sm"]
    query = update.callback_query
    sm.set_state(query.from_user.id, State.STEP_QUALITY)

    await query.edit_message_text(
        "📷 <b>Шаг 2 из 5</b>\n\nКакое качество камер вас интересует?",
        parse_mode="HTML",
        reply_markup=kb([
            [InlineKeyboardButton("📹 Стандартное (Full HD, 2 Мп)",  callback_data="quality:fullhd")],
            [InlineKeyboardButton("🎥 Высокое (4K, 8 Мп)",           callback_data="quality:4k")],
            [InlineKeyboardButton("🤷 Не знаю, посоветуйте",         callback_data="quality:any")],
        ])
    )


# ─────────────────────────────────────────
# Шаг 3: Место установки
# ─────────────────────────────────────────

async def show_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sm: StateManager = context.bot_data["sm"]
    query = update.callback_query
    sm.set_state(query.from_user.id, State.STEP_LOCATION)

    await query.edit_message_text(
        "🏠 <b>Шаг 3 из 5</b>\n\nГде будут установлены камеры?",
        parse_mode="HTML",
        reply_markup=kb([
            [InlineKeyboardButton("🌤 Только на улице",         callback_data="location:outdoor")],
            [InlineKeyboardButton("🏢 Только внутри помещений", callback_data="location:indoor")],
            [InlineKeyboardButton("🔀 И снаружи, и внутри",    callback_data="location:both")],
        ])
    )


# ─────────────────────────────────────────
# Шаг 4: Количество камер
# ─────────────────────────────────────────

async def show_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sm: StateManager = context.bot_data["sm"]
    query = update.callback_query
    sm.set_state(query.from_user.id, State.STEP_COUNT)

    await query.edit_message_text(
        "🔢 <b>Шаг 4 из 5</b>\n\nСколько камер нужно?",
        parse_mode="HTML",
        reply_markup=kb([
            [InlineKeyboardButton("1–2 камеры",   callback_data="count:1-2")],
            [InlineKeyboardButton("3–5 камер",    callback_data="count:3-5")],
            [InlineKeyboardButton("6–10 камер",   callback_data="count:6-10")],
            [InlineKeyboardButton("Больше 10",    callback_data="count:10+")],
        ])
    )


# ─────────────────────────────────────────
# Шаг 5: Срок хранения записи
# ─────────────────────────────────────────

async def show_storage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sm: StateManager = context.bot_data["sm"]
    query = update.callback_query
    sm.set_state(query.from_user.id, State.STEP_STORAGE)

    await query.edit_message_text(
        "💾 <b>Шаг 5 из 5</b>\n\nКак долго хранить видеозапись?",
        parse_mode="HTML",
        reply_markup=kb([
            [InlineKeyboardButton("7 дней",         callback_data="storage:7")],
            [InlineKeyboardButton("14 дней",        callback_data="storage:14")],
            [InlineKeyboardButton("30 дней",        callback_data="storage:30")],
            [InlineKeyboardButton("60+ дней",       callback_data="storage:60+")],
        ])
    )


# ─────────────────────────────────────────
# Шаг 6: Имя
# ─────────────────────────────────────────

async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sm: StateManager = context.bot_data["sm"]
    query = update.callback_query
    user_id = query.from_user.id
    sm.set_state(user_id, State.WAITING_NAME)

    # Пробуем взять имя из Telegram профиля
    tg_name = query.from_user.first_name or ""

    await query.edit_message_text(
        f"👤 Как вас зовут?\n\n"
        f"{'Можете нажать кнопку ниже или введите другое имя:' if tg_name else 'Введите ваше имя:'}",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(f"✅ {tg_name}", callback_data=f"name:{tg_name}")]]
            if tg_name else []
        ) if tg_name else None
    )


# ─────────────────────────────────────────
# Шаг 7: Телефон
# ─────────────────────────────────────────

async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sm: StateManager = context.bot_data["sm"]

    # Может прийти и как callback (имя выбрано кнопкой) и как обычное сообщение
    if update.callback_query:
        query = update.callback_query
        user_id = query.from_user.id
        sm.set_state(user_id, State.WAITING_PHONE)
        await query.edit_message_text(
            "📞 Введите ваш номер телефона:\n\n"
            "Например: <code>+7 900 000 00 00</code>",
            parse_mode="HTML",
        )
    else:
        user_id = update.effective_user.id
        sm.set_state(user_id, State.WAITING_PHONE)
        await update.message.reply_text(
            "📞 Введите ваш номер телефона:\n\n"
            "Например: <code>+7 900 000 00 00</code>",
            parse_mode="HTML",
        )


# ─────────────────────────────────────────
# Подтверждение
# ─────────────────────────────────────────

LABELS = {
    # distance
    "city":   "В черте города",
    "30km":   "До 30 км",
    "100km":  "30–100 км",
    "far":    "Более 100 км",
    # quality
    "fullhd": "Full HD (2 Мп)",
    "4k":     "4K (8 Мп)",
    "any":    "На ваш выбор",
    # location
    "outdoor": "На улице",
    "indoor":  "Внутри помещений",
    "both":    "И снаружи, и внутри",
    # storage
    "7":   "7 дней",
    "14":  "14 дней",
    "30":  "30 дней",
    "60+": "60+ дней",
}


async def show_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sm: StateManager = context.bot_data["sm"]
    user_id = update.effective_user.id
    sm.set_state(user_id, State.CONFIRM)

    order = sm.get_order(user_id, update.effective_chat.id)

    text = (
        "📋 <b>Проверьте вашу заявку:</b>\n\n"
        f"📍 Расположение: {LABELS.get(order.distance, order.distance)}\n"
        f"📷 Камеры: {LABELS.get(order.quality, order.quality)}\n"
        f"🏠 Установка: {LABELS.get(order.location, order.location)}\n"
        f"🔢 Количество: {order.camera_count}\n"
        f"💾 Хранение: {LABELS.get(order.storage, order.storage)}\n\n"
        f"👤 Имя: {order.client_name}\n"
        f"📞 Телефон: {order.client_phone}\n\n"
        "Всё верно?"
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Отправить заявку", callback_data="nav:confirm")],
            [InlineKeyboardButton("✏️ Начать заново",   callback_data="nav:restart")],
        ])
    )


# ─────────────────────────────────────────
# Отправка заявки
# ─────────────────────────────────────────

async def submit_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sm: StateManager = context.bot_data["sm"]
    query = update.callback_query
    user_id = query.from_user.id

    order = sm.get_order(user_id, update.effective_chat.id)
    order.completed_at = datetime.now()

    await query.edit_message_text("⏳ Отправляем заявку...")

    await send_to_telegram_group(context.bot, order)

    import asyncio
    await asyncio.get_event_loop().run_in_executor(None, send_email, order)

    sm.set_state(user_id, State.COMPLETED)
    sm.reset(user_id)

    await query.edit_message_text(
        "✅ <b>Заявка отправлена!</b>\n\n"
        f"Мы свяжемся с вами по номеру <b>{order.client_phone}</b> в ближайшее время.\n\n"
        "Спасибо, что выбрали Цифровые Телесистемы! 🙏\n\n"
        "/start — новый расчёт",
        parse_mode="HTML",
    )


# ─────────────────────────────────────────
# Роутер callback_query
# ─────────────────────────────────────────

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sm: StateManager = context.bot_data["sm"]
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data
    order = sm.get_order(user_id, update.effective_chat.id)

    # ── Навигация ──
    if data == "nav:to_distance":
        await show_distance(update, context)

    elif data == "nav:back":
        prev = sm.go_back(user_id)
        back_map = {
            State.STEP_DISTANCE: show_distance,
            State.STEP_QUALITY:  show_quality,
            State.STEP_LOCATION: show_location,
            State.STEP_COUNT:    show_count,
            State.STEP_STORAGE:  show_storage,
        }
        handler = back_map.get(prev)
        if handler:
            await handler(update, context)
        else:
            await query.edit_message_text("Используйте /start для начала.")

    elif data == "nav:confirm":
        await submit_order(update, context)

    elif data == "nav:restart":
        sm.reset(user_id)
        await query.edit_message_text("Хорошо, начнём заново. /start")

    # ── Шаг 1: расстояние ──
    elif data.startswith("distance:"):
        order.distance = data.split(":")[1]
        await show_quality(update, context)

    # ── Шаг 2: качество ──
    elif data.startswith("quality:"):
        order.quality = data.split(":")[1]
        await show_location(update, context)

    # ── Шаг 3: место ──
    elif data.startswith("location:"):
        order.location = data.split(":")[1]
        await show_count(update, context)

    # ── Шаг 4: количество ──
    elif data.startswith("count:"):
        order.camera_count = data.split(":")[1]
        await show_storage(update, context)

    # ── Шаг 5: хранение ──
    elif data.startswith("storage:"):
        order.storage = data.split(":")[1]
        await ask_name(update, context)

    # ── Имя из профиля Telegram ──
    elif data.startswith("name:"):
        order.client_name = data.split(":", 1)[1]
        await ask_phone(update, context)


# ─────────────────────────────────────────
# Обработчик текстовых сообщений
# ─────────────────────────────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sm: StateManager = context.bot_data["sm"]
    user_id = update.effective_user.id
    state = sm.get_state(user_id)
    text = update.message.text.strip()
    order = sm.get_order(user_id, update.effective_chat.id)

    if state == State.WAITING_NAME:
        order.client_name = text
        await ask_phone(update, context)

    elif state == State.WAITING_PHONE:
        order.client_phone = text
        await show_confirm(update, context)

    else:
        await update.message.reply_text(
            "Используйте /start для начала подбора."
        )