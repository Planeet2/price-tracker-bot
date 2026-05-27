import html
import requests

from app.config import settings


def send_telegram_message(text: str) -> None:
    if not settings.bot_token or not settings.my_chat_id:
        print("Telegram не настроен: BOT_TOKEN или MY_CHAT_ID пустой")
        return

    url = f"https://api.telegram.org/bot{settings.bot_token}/sendMessage"
    payload = {
        "chat_id": settings.my_chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    response = requests.post(url, data=payload, timeout=20)
    response.raise_for_status()


def build_discount_message(name: str, old_price: float, new_price: int, url: str, target_price=None) -> str:
    diff = old_price - new_price
    percent = diff / old_price * 100 if old_price else 0
    safe_name = html.escape(name)
    target_line = ""

    if target_price:
        status = "✅ ниже цели" if new_price <= float(target_price) else "⏳ выше цели"
        target_line = f"\n🎯 Целевая цена: <b>{int(target_price):,} ₽</b> — {status}".replace(",", " ")

    message = f"""
🔥 <b>Цена снизилась!</b>

📦 <b>{safe_name}</b>
📉 Было: <s>{int(old_price):,} ₽</s>
💰 Стало: <b>{new_price:,} ₽</b>
📊 Скидка: <b>{percent:.1f}%</b>
💵 Экономия: <b>{int(diff):,} ₽</b>{target_line}

<a href="{html.escape(url)}">Открыть товар</a>
""".replace(",", " ").strip()

    return message
