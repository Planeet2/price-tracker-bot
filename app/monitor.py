import time

from app.config import settings
from app.database import (
    get_active_products,
    get_last_price,
    init_db,
    save_price,
    upsert_product,
)
from app.notifier import build_discount_message, send_telegram_message
from app.scraper import scrape_product


def check_one_product(url: str, target_price=None) -> dict:
    product = scrape_product(url)
    product_id = upsert_product(
        external_id=product.external_id,
        name=product.name,
        url=product.url,
        target_price=target_price,
    )

    old_price = get_last_price(product_id)
    save_price(product_id, product.price)

    is_discount = old_price is not None and product.price < old_price
    is_target_reached = target_price is not None and product.price <= float(target_price)

    if is_discount or is_target_reached:
        message = build_discount_message(
            name=product.name,
            old_price=old_price or product.price,
            new_price=product.price,
            url=product.url,
            target_price=target_price,
        )
        send_telegram_message(message)

    return {
        "product_id": product_id,
        "name": product.name,
        "price": product.price,
        "old_price": old_price,
        "is_discount": is_discount,
        "is_target_reached": is_target_reached,
    }


def run_cycle() -> None:
    products = get_active_products()
    if not products:
        print("Нет активных товаров. Добавь товар через Telegram-команду /add <url>")
        return

    for product in products:
        try:
            result = check_one_product(product["url"], product.get("target_price"))
            print(f"OK: {result['name']} — {result['price']} ₽")
        except Exception as exc:
            print(f"Ошибка при проверке {product['url']}: {exc}")


def main() -> None:
    init_db()
    while True:
        print(f"\n[{time.strftime('%H:%M:%S')}] Запуск мониторинга...")
        run_cycle()
        print(f"Проверка завершена. Следующий запуск через {settings.check_interval_seconds} сек.")
        time.sleep(settings.check_interval_seconds)


if __name__ == "__main__":
    main()
