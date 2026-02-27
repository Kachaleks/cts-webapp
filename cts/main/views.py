import json
import logging
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import render
from .models import Camera, CableSettings

logger = logging.getLogger(__name__)

# вынес все что можно в настройки. Чтоб не в 10 местах менять а в одном. 
BOT_TOKEN          = os.getenv("BOT_TOKEN", "")
MANAGERS_GROUP_ID  = os.getenv("MANAGERS_GROUP_ID", "")
SMTP_HOST          = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT          = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER          = os.getenv("SMTP_USER", "")
SMTP_PASSWORD      = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM         = os.getenv("EMAIL_FROM", SMTP_USER)
EMAIL_TO           = os.getenv("EMAIL_TO", "")


def calculator(request):
    cameras = Camera.objects.all()
    cables_settings = CableSettings.objects.filter(is_active=True).first()
    cable_price_per_meter = cables_settings.price_per_meter if cables_settings else 0

    resolutions = cameras.values_list('resolution', flat=True).distinct()
    types = cameras.values_list('type', flat=True).distinct()
    night_vision_technologies = cameras.values_list('night_vision_technology', flat=True).distinct()
    connection_types = cameras.values_list('connection_type', flat=True).distinct()
    lens = cameras.values_list('lens', flat=True).distinct()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if 'resolution' in request.GET:
            cameras = cameras.filter(resolution=int(request.GET['resolution']))
        if 'type' in request.GET:
            cameras = cameras.filter(type=request.GET['type'])
        if 'night_vision_technology' in request.GET:
            cameras = cameras.filter(night_vision_technology=request.GET['night_vision_technology'])
        if 'connection_types' in request.GET:
            cameras = cameras.filter(connection_type=request.GET['connection_types'])  # исправлен баг
        if 'lens' in request.GET:
            lens_values = request.GET.getlist('lens')
            if lens_values:
                cameras = cameras.filter(lens__in=lens_values)
        if 'has_zoom' in request.GET:
            cameras = cameras.filter(has_zoom=request.GET['has_zoom'].lower() == 'true')
        if 'has_people_analytics' in request.GET:
            cameras = cameras.filter(has_people_analytics=True)
        if 'has_cars_analytics' in request.GET:
            cameras = cameras.filter(has_cars_analytics=True)
        if 'has_special_cars_analytics' in request.GET:
            cameras = cameras.filter(has_special_cars_analytics=True)
        if 'has_micro' in request.GET:
            cameras = cameras.filter(has_micro=True)
        if 'has_dynamic' in request.GET:
            cameras = cameras.filter(has_dynamic=True)

        data = {
            'cameras': [
                {
                    'id': c.id,
                    'name': c.name,
                    'type': c.type,
                    'resolution': c.resolution,
                    'connection_type': c.connection_type,
                    'price': c.price,
                    'picture': c.picture.url if c.picture else '',
                    'has_micro': c.has_micro,
                    'has_zoom': c.has_zoom,
                    'has_dynamic': c.has_dynamic,
                }
                for c in cameras
            ],
            'cable_price': cable_price_per_meter,
        }
        return JsonResponse(data)

    context = {
        'cameras': cameras,
        'resolutions': resolutions,
        'types': types,
        'night_vision_technologies': night_vision_technologies,
        'connection_types': connection_types,
        'lens': lens,
        'installation_price': cable_price_per_meter,
    }
    return render(request, 'main/calculator.html', context)


@csrf_exempt
@require_POST
def send_order(request):
    """
    Принимает JSON-заявку с сайта, форматирует и отправляет:
    - в Telegram группу менеджеров (напрямую через Bot API)
    - на email

    Ожидаемый JSON:
    {
        "client_name": "Иван",
        "client_phone": "+7 900 000 00 00",
        "cameras": [
            {"id": 1, "name": "HiWatch ...", "price": 4500, "quantity": 2, "cable_meters": 15}
        ],
        "cable_price_per_meter": 125,
        "totals": {
            "cameras_total": 9000,
            "cable_meters": 30,
            "cable_total": 3750,
            "installation_total": 3750,
            "grand_total": 16500
        }
    }
    """
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Invalid JSON"}, status=400)

    client_name  = body.get("client_name", "—")
    client_phone = body.get("client_phone", "—")
    cameras      = body.get("cameras", [])
    totals       = body.get("totals", {})
    cable_price  = body.get("cable_price_per_meter", 0)

    if not cameras:
        return JsonResponse({"ok": False, "error": "Корзина пуста"}, status=400)

    tg_text  = _format_telegram(client_name, client_phone, cameras, totals, cable_price)
    txt_text = _format_plaintext(client_name, client_phone, cameras, totals, cable_price)

    errors = []

    # Отправка в Telegram
    if BOT_TOKEN and MANAGERS_GROUP_ID:
        ok, err = _send_telegram(tg_text)
        if not ok:
            errors.append(f"Telegram: {err}")
            logger.error(f"Ошибка отправки в Telegram: {err}")
    else:
        logger.warning("BOT_TOKEN или MANAGERS_GROUP_ID не настроен")

    # Отправка email
    if SMTP_USER and EMAIL_TO:
        ok, err = _send_email(client_name, txt_text)
        if not ok:
            errors.append(f"Email: {err}")
            logger.error(f"Ошибка отправки email: {err}")
    else:
        logger.warning("Email не настроен")

    if errors:
        return JsonResponse({"ok": False, "errors": errors}, status=500)

    return JsonResponse({"ok": True})


def _format_telegram(client_name, client_phone, cameras, totals, cable_price) -> str:
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    lines = [
        f"🔔 <b>НОВАЯ ЗАЯВКА</b> [САЙТ]",
        f"🕐 {now}",
        "",
        "👤 <b>Клиент:</b>",
        f"  Имя: {client_name}",
        f"  Телефон: {client_phone}",
        "",
        "📦 <b>Состав заказа:</b>",
    ]
    for cam in cameras:
        qty = cam.get("quantity", 1)
        price = cam.get("price", 0)
        cable = cam.get("cable_meters", 0)
        total = price * qty
        cable_info = f", кабель {cable} м × {qty} = {cable * qty} м" if cable else ""
        lines.append(
            f"  • {cam.get('name')}\n"
            f"    {qty} шт. × {price:,} ₽ = {total:,} ₽{cable_info}"
        )

    lines += ["", "💰 <b>Итого:</b>",
              f"  Камеры: {totals.get('cameras_total', 0):,} ₽"]

    cable_meters = totals.get("cable_meters", 0)
    if cable_meters:
        lines += [
            f"  Кабель ({cable_meters} м × {cable_price} ₽): {totals.get('cable_total', 0):,} ₽",
            f"  Монтаж: {totals.get('installation_total', 0):,} ₽",
        ]

    lines += ["", f"  <b>ИТОГО: {totals.get('grand_total', 0):,} ₽</b>"]
    return "\n".join(lines)


def _format_plaintext(client_name, client_phone, cameras, totals, cable_price) -> str:
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    lines = [
        f"НОВАЯ ЗАЯВКА [САЙТ] — {now}",
        "=" * 50,
        f"Клиент: {client_name}",
        f"Телефон: {client_phone}",
        "",
        "СОСТАВ ЗАКАЗА:",
    ]
    for cam in cameras:
        qty = cam.get("quantity", 1)
        price = cam.get("price", 0)
        cable = cam.get("cable_meters", 0)
        lines.append(f"  {cam.get('name')} — {qty} шт. × {price:,} руб. = {price * qty:,} руб.")
        if cable:
            lines.append(f"    Кабель: {cable} м × {qty} = {cable * qty} м")
    lines += [
        "",
        f"Камеры: {totals.get('cameras_total', 0):,} руб.",
    ]
    if totals.get("cable_meters"):
        lines += [
            f"Кабель: {totals.get('cable_total', 0):,} руб.",
            f"Монтаж: {totals.get('installation_total', 0):,} руб.",
        ]
    lines.append(f"ИТОГО: {totals.get('grand_total', 0):,} руб.")
    return "\n".join(lines)


def _send_telegram(text: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        resp = requests.post(url, json={
            "chat_id": MANAGERS_GROUP_ID,
            "text": text,
            "parse_mode": "HTML",
        }, timeout=10)
        data = resp.json()
        if data.get("ok"):
            return True, None
        return False, data.get("description", "unknown error")
    except Exception as e:
        return False, str(e)


def _send_email(client_name: str, body: str):
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Новая заявка от {client_name} — Цифровые Телесистемы"
        msg["From"] = EMAIL_FROM
        msg["To"] = EMAIL_TO
        msg.attach(MIMEText(body, "plain", "utf-8"))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        return True, None
    except Exception as e:
        return False, str(e)