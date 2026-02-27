# bot/handlers.py
"""
Обработчики бота: пошаговый калькулятор с inline-кнопками,
выбор камер из БД, корзина, контакты, отправка заявки.
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import db
from state_manager import StateManager, State
from models import BotOrder
from notifier import send_to_telegram_group, send_email

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Вспомогательные функции для клавиатур
# ──────────────────────────────────────────────

def _back_skip_buttons(skip_data: str = None) -> list:
    """Строка кнопок Назад / Пропустить"""
    row = [InlineKeyboardButton("⬅️ Назад", callback_data="nav:back")]
    if skip_data:
        row.append(InlineKeyboardButton("Пропустить ➡️", callback_data=skip_data))
    return row


def _build_keyboard(buttons: list, back_skip_data: str = None) -> InlineKeyboardMarkup:
    """Собирает клавиатуру: кнопки + строка назад/пропустить внизу"""
    keyboard = buttons[:]
    keyboard.append(_back_skip_buttons(back_skip_data))
    return InlineKeyboardMarkup(keyboard)


# ──────────────────────────────────────────────
# Шаг 1: /start — приветствие
# ──────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sm: StateManager = context.bot_data["sm"]
    user_id = update.effective_user.id
    sm.reset(user_id)
    sm.set_state(user_id, State.START)

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("📷 Подобрать камеры", callback_data="nav:to_filter_type")
    ]])
    await update.message.reply_text(
        "👋 <b>Добро пожаловать в калькулятор видеонаблюдения!</b>\n\n"
        "Я помогу подобрать камеры под ваш объект и рассчитаю стоимость.\n\n"
        "Нажмите кнопку, чтобы начать:",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sm: StateManager = context.bot_data["sm"]
    sm.reset(update.effective_user.id)
    await update.message.reply_text("❌ Расчёт отменён. /start — начать заново.")


# ──────────────────────────────────────────────
# Шаг 2: Тип камеры
# ──────────────────────────────────────────────

async def show_filter_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sm: StateManager = context.bot_data["sm"]
    query = update.callback_query
    user_id = update.effective_user.id
    sm.set_state(user_id, State.FILTER_TYPE)

    types = db.get_distinct_values("type")
    buttons = [
        [InlineKeyboardButton(t, callback_data=f"type:{t}")]
        for t in types
    ]
    buttons.append(_back_skip_buttons("nav:to_filter_connection"))

    await query.edit_message_text(
        "📷 <b>Шаг 1 из 5</b> — Выберите тип камеры:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


# ──────────────────────────────────────────────
# Шаг 3: Тип подключения (улица/помещение)
# ──────────────────────────────────────────────

async def show_filter_connection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sm: StateManager = context.bot_data["sm"]
    query = update.callback_query
    user_id = update.effective_user.id
    sm.set_state(user_id, State.FILTER_CONNECTION)

    connections = db.get_distinct_values("connection_type")
    buttons = [
        [InlineKeyboardButton(c, callback_data=f"connection:{c}")]
        for c in connections
    ]
    buttons.append(_back_skip_buttons("nav:to_filter_resolution"))

    await query.edit_message_text(
        "🔌 <b>Шаг 2 из 5</b> — Тип подключения / место установки:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


# ──────────────────────────────────────────────
# Шаг 4: Разрешение
# ──────────────────────────────────────────────

async def show_filter_resolution(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sm: StateManager = context.bot_data["sm"]
    query = update.callback_query
    user_id = update.effective_user.id
    sm.set_state(user_id, State.FILTER_RESOLUTION)

    resolutions = db.get_distinct_values("resolution")
    buttons = [
        [InlineKeyboardButton(f"{r} Мп", callback_data=f"resolution:{r}")]
        for r in resolutions
    ]
    buttons.append(_back_skip_buttons("nav:to_filter_night_vision"))

    await query.edit_message_text(
        "📺 <b>Шаг 3 из 5</b> — Разрешение камеры:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


# ──────────────────────────────────────────────
# Шаг 5: Ночное видение
# ──────────────────────────────────────────────

async def show_filter_night_vision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sm: StateManager = context.bot_data["sm"]
    query = update.callback_query
    user_id = update.effective_user.id
    sm.set_state(user_id, State.FILTER_NIGHT_VISION)

    nvs = db.get_distinct_values("night_vision_technology")
    buttons = [
        [InlineKeyboardButton(n, callback_data=f"nightvision:{n}")]
        for n in nvs
    ]
    buttons.append(_back_skip_buttons("nav:to_filter_options"))

    await query.edit_message_text(
        "🌙 <b>Шаг 4 из 5</b> — Технология ночного видения:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


# ──────────────────────────────────────────────
# Шаг 6: Доп. опции (чекбоксы через toggle)
# ──────────────────────────────────────────────

async def show_filter_options(update: Update, context: ContextTypes.DEFAULT_TYPE,
                               order: BotOrder = None):
    sm: StateManager = context.bot_data["sm"]
    query = update.callback_query
    user_id = update.effective_user.id
    sm.set_state(user_id, State.FILTER_OPTIONS)

    if order is None:
        order = sm.get_order(user_id, update.effective_chat.id)

    def check(val): return "✅" if val else "⬜"

    buttons = [
        [InlineKeyboardButton(
            f"{check(order.filter_has_micro)} Микрофон",
            callback_data="opt:has_micro"
        )],
        [InlineKeyboardButton(
            f"{check(order.filter_has_zoom)} Зум",
            callback_data="opt:has_zoom"
        )],
        [InlineKeyboardButton(
            f"{check(order.filter_has_people_analytics)} Аналитика: люди",
            callback_data="opt:has_people_analytics"
        )],
        [InlineKeyboardButton(
            f"{check(order.filter_has_cars_analytics)} Аналитика: транспорт",
            callback_data="opt:has_cars_analytics"
        )],
        [InlineKeyboardButton("🔍 Показать камеры", callback_data="nav:to_camera_list")],
        _back_skip_buttons(),
    ]

    await query.edit_message_text(
        "⚙️ <b>Шаг 5 из 5</b> — Дополнительные опции:\n\n"
        "Нажмите чтобы включить/выключить, затем «Показать камеры»:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


# ──────────────────────────────────────────────
# Шаг 7: Список камер
# ──────────────────────────────────────────────

async def show_camera_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sm: StateManager = context.bot_data["sm"]
    query = update.callback_query
    user_id = update.effective_user.id
    sm.set_state(user_id, State.CAMERA_LIST)

    order = sm.get_order(user_id, update.effective_chat.id)
    filters = order.get_active_filters()
    cameras = db.get_all_cameras(filters)

    if not cameras:
        buttons = [
            [InlineKeyboardButton("🔄 Сбросить фильтры", callback_data="nav:reset_filters")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="nav:back")],
        ]
        await query.edit_message_text(
            "😔 По вашим фильтрам камер не найдено.\n\nПопробуйте сбросить часть фильтров.",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return

    # Показываем камеры кнопками. Если уже в корзине — показываем кол-во
    buttons = []
    for cam in cameras:
        item = order.get_cart_item(cam.id)
        qty_label = f" [{item.quantity} шт.]" if item else ""
        buttons.append([
            InlineKeyboardButton(
                f"{cam.name} — {cam.price:,} ₽{qty_label}",
                callback_data=f"select_camera:{cam.id}"
            )
        ])

    # Кнопка корзины если что-то добавлено
    if not order.is_cart_empty():
        total_items = sum(i.quantity for i in order.cart)
        buttons.append([
            InlineKeyboardButton(
                f"🛒 Корзина ({total_items} шт.) → Оформить",
                callback_data="nav:to_cart"
            )
        ])

    buttons.append([InlineKeyboardButton("⬅️ Изменить фильтры", callback_data="nav:to_filter_options")])

    filters_text = _format_active_filters(order)
    await query.edit_message_text(
        f"📋 <b>Найдено камер: {len(cameras)}</b>\n"
        f"{filters_text}\n\n"
        "Нажмите на камеру чтобы добавить в заказ:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


def _format_active_filters(order: BotOrder) -> str:
    parts = []
    if order.filter_type:
        parts.append(f"Тип: {order.filter_type}")
    if order.filter_connection:
        parts.append(f"Подключение: {order.filter_connection}")
    if order.filter_resolution:
        parts.append(f"Разрешение: {order.filter_resolution} Мп")
    if order.filter_night_vision:
        parts.append(f"Ночное видение: {order.filter_night_vision}")
    if order.filter_has_micro:
        parts.append("Микрофон: ✅")
    if order.filter_has_zoom:
        parts.append("Зум: ✅")
    if order.filter_has_people_analytics:
        parts.append("Аналитика люди: ✅")
    if order.filter_has_cars_analytics:
        parts.append("Аналитика ТС: ✅")
    if not parts:
        return ""
    return "🔍 Фильтры: " + ", ".join(parts)


# ──────────────────────────────────────────────
# Шаг 8: Выбор камеры → ввод количества
# ──────────────────────────────────────────────

async def show_camera_detail(update: Update, context: ContextTypes.DEFAULT_TYPE,
                              camera_id: int):
    sm: StateManager = context.bot_data["sm"]
    query = update.callback_query
    user_id = update.effective_user.id

    camera = db.get_camera_by_id(camera_id)
    if not camera:
        await query.answer("Камера не найдена")
        return

    order = sm.get_order(user_id, update.effective_chat.id)
    order.pending_camera_id = camera_id
    sm.set_state(user_id, State.CAMERA_QUANTITY)

    existing = order.get_cart_item(camera_id)
    current_qty = existing.quantity if existing else 0

    specs = []
    specs.append(f"Разрешение: {camera.resolution} Мп")
    specs.append(f"Тип: {camera.type}")
    specs.append(f"Подключение: {camera.connection_type}")
    specs.append(f"Ночное видение: {camera.night_vision_technology}")
    if camera.has_micro: specs.append("Микрофон: ✅")
    if camera.has_zoom: specs.append("Зум: ✅")
    if camera.has_people_analytics: specs.append("Аналитика люди: ✅")
    if camera.has_cars_analytics: specs.append("Аналитика ТС: ✅")
    if camera.description: specs.append(f"\n{camera.description}")

    text = (
        f"📷 <b>{camera.name}</b>\n"
        f"💰 <b>{camera.price:,} ₽</b>\n\n"
        f"{chr(10).join(specs)}\n\n"
        f"{'Уже в корзине: ' + str(current_qty) + ' шт.' + chr(10) if current_qty else ''}"
        f"Введите количество камер (или 0 чтобы убрать из корзины):"
    )

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ К списку камер", callback_data="nav:to_camera_list")]
    ])

    await query.edit_message_text(text, parse_mode="HTML", reply_markup=buttons)


# ──────────────────────────────────────────────
# Шаг 9: Ввод метров кабеля
# ──────────────────────────────────────────────

async def ask_cable_meters(update: Update, context: ContextTypes.DEFAULT_TYPE,
                            camera_id: int, quantity: int):
    sm: StateManager = context.bot_data["sm"]
    user_id = update.effective_user.id
    sm.set_state(user_id, State.CAMERA_CABLE)

    camera = db.get_camera_by_id(camera_id)
    cable_price = db.get_cable_price()

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("0 м (без кабеля)", callback_data=f"cable:{camera_id}:{quantity}:0")],
        [InlineKeyboardButton("⬅️ Назад", callback_data=f"select_camera:{camera_id}")],
    ])

    await update.message.reply_text(
        f"📏 Сколько метров кабеля нужно для <b>{camera.name}</b>?\n\n"
        f"Цена кабеля: {cable_price} ₽/м\n"
        f"(Монтаж кабеля входит в стоимость)\n\n"
        f"Введите число метров или нажмите «0 м»:",
        parse_mode="HTML",
        reply_markup=buttons,
    )


# ──────────────────────────────────────────────
# Шаг 10: Корзина
# ──────────────────────────────────────────────

async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sm: StateManager = context.bot_data["sm"]
    query = update.callback_query
    user_id = update.effective_user.id
    sm.set_state(user_id, State.CART_VIEW)

    order = sm.get_order(user_id, update.effective_chat.id)
    cable_price = db.get_cable_price()

    if order.is_cart_empty():
        await query.edit_message_text(
            "🛒 Корзина пуста. Выберите камеры.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("← К камерам", callback_data="nav:to_camera_list")
            ]])
        )
        return

    totals = order.calculate_total(cable_price)
    lines = ["🛒 <b>Ваш заказ:</b>\n"]

    for item in order.cart:
        lines.append(f"• <b>{item.camera_name}</b>")
        lines.append(f"  {item.quantity} шт. × {item.camera_price:,} ₽ = {item.cameras_total:,} ₽")
        if item.cable_meters > 0:
            lines.append(f"  Кабель: {item.cable_meters} м × {item.quantity} = {item.cable_meters * item.quantity} м")

    lines += [
        "",
        f"💰 Камеры: {totals['cameras_total']:,} ₽",
    ]
    if totals["cable_meters"] > 0:
        lines += [
            f"🔌 Кабель ({totals['cable_meters']} м): {totals['cable_total']:,} ₽",
            f"🔧 Монтаж: {totals['installation_total']:,} ₽",
        ]
    lines.append(f"\n<b>ИТОГО: {totals['grand_total']:,} ₽</b>")

    buttons = [
        [InlineKeyboardButton("✅ Оформить заявку", callback_data="nav:to_order")],
        [InlineKeyboardButton("← Добавить ещё камеры", callback_data="nav:to_camera_list")],
    ]

    await query.edit_message_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


# ──────────────────────────────────────────────
# Шаг 11: Имя клиента
# ──────────────────────────────────────────────

async def ask_client_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sm: StateManager = context.bot_data["sm"]
    query = update.callback_query
    user_id = update.effective_user.id
    sm.set_state(user_id, State.WAITING_NAME)

    await query.edit_message_text(
        "👤 Как вас зовут?\n\nВведите имя:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("⬅️ К корзине", callback_data="nav:to_cart")
        ]])
    )


# ──────────────────────────────────────────────
# Шаг 12: Телефон клиента
# ──────────────────────────────────────────────

async def ask_client_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sm: StateManager = context.bot_data["sm"]
    user_id = update.effective_user.id
    sm.set_state(user_id, State.WAITING_PHONE)

    await update.message.reply_text(
        f"📞 Введите ваш номер телефона\n"
        f"(например: +7 900 000 00 00):",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("⬅️ Назад", callback_data="nav:back")
        ]])
    )


# ──────────────────────────────────────────────
# Шаг 13: Подтверждение и отправка
# ──────────────────────────────────────────────

async def show_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sm: StateManager = context.bot_data["sm"]
    user_id = update.effective_user.id
    sm.set_state(user_id, State.CONFIRM)

    order = sm.get_order(user_id, update.effective_chat.id)
    cable_price = db.get_cable_price()
    totals = order.calculate_total(cable_price)

    text = (
        f"📋 <b>Подтвердите заявку:</b>\n\n"
        f"👤 Имя: {order.client_name}\n"
        f"📞 Телефон: {order.client_phone}\n\n"
        f"💰 Итого: <b>{totals['grand_total']:,} ₽</b>\n\n"
        f"Отправить заявку менеджеру?"
    )

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Отправить заявку", callback_data="nav:confirm_order")],
        [InlineKeyboardButton("✏️ Изменить данные", callback_data="nav:to_order")],
    ])

    await update.message.reply_text(text, parse_mode="HTML", reply_markup=buttons)


# ──────────────────────────────────────────────
# Финал: отправка заявки
# ──────────────────────────────────────────────

async def submit_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sm: StateManager = context.bot_data["sm"]
    query = update.callback_query
    user_id = update.effective_user.id

    order = sm.get_order(user_id, update.effective_chat.id)
    order.completed_at = __import__("datetime").datetime.now()
    cable_price = db.get_cable_price()

    await query.edit_message_text("⏳ Отправляем заявку...")

    # Отправка в группу менеджеров
    await send_to_telegram_group(context.bot, order, cable_price, source="бот")

    # Email в отдельном потоке чтобы не блокировать
    import asyncio
    await asyncio.get_event_loop().run_in_executor(
        None, send_email, order, cable_price, "бот"
    )

    sm.set_state(user_id, State.COMPLETED)

    await query.edit_message_text(
        "✅ <b>Заявка отправлена!</b>\n\n"
        f"Наш менеджер свяжется с вами по номеру {order.client_phone} "
        f"в ближайшее время.\n\n"
        "Спасибо, что выбрали Цифровые Телесистемы! 🙏\n\n"
        "/start — новый расчёт",
        parse_mode="HTML",
    )

    sm.reset(user_id)


# ──────────────────────────────────────────────
# Главный роутер callback_query
# ──────────────────────────────────────────────

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sm: StateManager = context.bot_data["sm"]
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    data = query.data
    order = sm.get_order(user_id, update.effective_chat.id)

    # ── Навигация ──
    if data == "nav:to_filter_type":
        await show_filter_type(update, context)

    elif data == "nav:to_filter_connection":
        await show_filter_connection(update, context)

    elif data == "nav:to_filter_resolution":
        await show_filter_resolution(update, context)

    elif data == "nav:to_filter_night_vision":
        await show_filter_night_vision(update, context)

    elif data == "nav:to_filter_options":
        await show_filter_options(update, context, order)

    elif data == "nav:to_camera_list":
        await show_camera_list(update, context)

    elif data == "nav:to_cart":
        await show_cart(update, context)

    elif data == "nav:to_order":
        await ask_client_name(update, context)

    elif data == "nav:confirm_order":
        await submit_order(update, context)

    elif data == "nav:reset_filters":
        order.filter_type = None
        order.filter_connection = None
        order.filter_resolution = None
        order.filter_night_vision = None
        order.filter_has_micro = False
        order.filter_has_zoom = False
        order.filter_has_people_analytics = False
        order.filter_has_cars_analytics = False
        await show_filter_type(update, context)

    elif data == "nav:back":
        prev = sm.go_back(user_id)
        if prev:
            # Переход назад по состоянию
            back_map = {
                State.FILTER_TYPE: show_filter_type,
                State.FILTER_CONNECTION: show_filter_connection,
                State.FILTER_RESOLUTION: show_filter_resolution,
                State.FILTER_NIGHT_VISION: show_filter_night_vision,
                State.FILTER_OPTIONS: show_filter_options,
                State.CAMERA_LIST: show_camera_list,
                State.CART_VIEW: show_cart,
            }
            handler = back_map.get(prev)
            if handler:
                await handler(update, context)
            else:
                await query.edit_message_text("Используйте /start для начала.")
        else:
            await query.edit_message_text("Вы в начале. Используйте /start.")

    # ── Выбор фильтра: тип камеры ──
    elif data.startswith("type:"):
        order.filter_type = data.split(":", 1)[1]
        await show_filter_connection(update, context)

    # ── Выбор фильтра: подключение ──
    elif data.startswith("connection:"):
        order.filter_connection = data.split(":", 1)[1]
        await show_filter_resolution(update, context)

    # ── Выбор фильтра: разрешение ──
    elif data.startswith("resolution:"):
        order.filter_resolution = int(data.split(":", 1)[1])
        await show_filter_night_vision(update, context)

    # ── Выбор фильтра: ночное видение ──
    elif data.startswith("nightvision:"):
        order.filter_night_vision = data.split(":", 1)[1]
        await show_filter_options(update, context, order)

    # ── Тогл доп. опций ──
    elif data.startswith("opt:"):
        opt = data.split(":", 1)[1]
        if opt == "has_micro":
            order.filter_has_micro = not order.filter_has_micro
        elif opt == "has_zoom":
            order.filter_has_zoom = not order.filter_has_zoom
        elif opt == "has_people_analytics":
            order.filter_has_people_analytics = not order.filter_has_people_analytics
        elif opt == "has_cars_analytics":
            order.filter_has_cars_analytics = not order.filter_has_cars_analytics
        await show_filter_options(update, context, order)

    # ── Выбор камеры из списка ──
    elif data.startswith("select_camera:"):
        camera_id = int(data.split(":")[1])
        await show_camera_detail(update, context, camera_id)

    # ── Выбор кабеля через кнопку (0 м) ──
    elif data.startswith("cable:"):
        _, cam_id, qty, meters = data.split(":")
        cam_id, qty, meters = int(cam_id), int(qty), int(meters)
        camera = db.get_camera_by_id(cam_id)
        if camera and qty > 0:
            order.add_to_cart(cam_id, camera.name, camera.price, qty, meters)
        elif qty == 0:
            order.remove_from_cart(cam_id)
        await show_camera_list(update, context)


# ──────────────────────────────────────────────
# Обработчик текстовых сообщений
# ──────────────────────────────────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sm: StateManager = context.bot_data["sm"]
    user_id = update.effective_user.id
    state = sm.get_state(user_id)
    text = update.message.text.strip()
    order = sm.get_order(user_id, update.effective_chat.id)

    # Ввод количества камер
    if state == State.CAMERA_QUANTITY:
        try:
            qty = int(text)
            if qty < 0:
                raise ValueError
            camera_id = order.pending_camera_id
            if camera_id is None:
                await update.message.reply_text("Ошибка: камера не выбрана. /start")
                return
            if qty == 0:
                order.remove_from_cart(camera_id)
                await update.message.reply_text("Камера убрана из корзины.")
                # показываем список заново через фейковый callback
                await _show_camera_list_message(update, context, order)
                return
            # Спрашиваем метры кабеля
            await ask_cable_meters(update, context, camera_id, qty)
        except ValueError:
            await update.message.reply_text("⚠️ Введите целое число (0 или больше)")

    # Ввод метров кабеля
    elif state == State.CAMERA_CABLE:
        try:
            meters = int(text)
            if meters < 0:
                raise ValueError
            camera_id = order.pending_camera_id
            # Количество берём из предыдущего сообщения — храним в контексте
            qty = context.user_data.get("pending_qty", 1)
            camera = db.get_camera_by_id(camera_id)
            if camera:
                order.add_to_cart(camera_id, camera.name, camera.price, qty, meters)
                cable_price = db.get_cable_price()
                cable_cost = meters * qty * cable_price
                await update.message.reply_text(
                    f"✅ Добавлено: <b>{camera.name}</b> × {qty} шт.\n"
                    f"Кабель: {meters} м × {qty} = {meters * qty} м "
                    f"({cable_cost:,} ₽)\n\n"
                    f"Продолжите выбор или перейдите в корзину.",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🛒 Корзина", callback_data="nav:to_cart")],
                        [InlineKeyboardButton("← Ещё камеры", callback_data="nav:to_camera_list")],
                    ])
                )
        except ValueError:
            await update.message.reply_text("⚠️ Введите целое число метров (0 или больше)")

    # Ввод имени
    elif state == State.WAITING_NAME:
        order.client_name = text
        await ask_client_phone(update, context)

    # Ввод телефона
    elif state == State.WAITING_PHONE:
        order.client_phone = text
        await show_confirm(update, context)

    else:
        await update.message.reply_text(
            "Используйте /start для начала расчёта."
        )


async def _show_camera_list_message(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                     order: BotOrder):
    """Показывает список камер через обычное сообщение (не callback)"""
    cable_price = db.get_cable_price()
    cameras = db.get_all_cameras(order.get_active_filters())

    buttons = []
    for cam in cameras:
        item = order.get_cart_item(cam.id)
        qty_label = f" [{item.quantity} шт.]" if item else ""
        buttons.append([
            InlineKeyboardButton(
                f"{cam.name} — {cam.price:,} ₽{qty_label}",
                callback_data=f"select_camera:{cam.id}"
            )
        ])

    if not order.is_cart_empty():
        total_items = sum(i.quantity for i in order.cart)
        buttons.append([
            InlineKeyboardButton(
                f"🛒 Корзина ({total_items} шт.) → Оформить",
                callback_data="nav:to_cart"
            )
        ])

    buttons.append([InlineKeyboardButton("← Изменить фильтры", callback_data="nav:to_filter_options")])

    await update.message.reply_text(
        f"📋 Найдено камер: {len(cameras)}\nВыберите камеры для заказа:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


# ──────────────────────────────────────────────
# Хранение pending_qty в user_data при вводе кол-ва
# (патч: перехватываем handle_message для сохранения qty)
# ──────────────────────────────────────────────

# Переопределяем ask_cable_meters чтобы сохранить qty в user_data
_original_ask_cable = ask_cable_meters

async def ask_cable_meters(update: Update, context: ContextTypes.DEFAULT_TYPE,
                            camera_id: int, quantity: int):
    context.user_data["pending_qty"] = quantity
    await _original_ask_cable(update, context, camera_id, quantity)