import os
from dotenv import load_dotenv
load_dotenv()
import psycopg2
from playwright.sync_api import sync_playwright
import time
import requests

TOKEN = os.getenv("BOT_TOKEN")
MY_CHAT_ID = os.getenv("MY_CHAT_ID")


def send_telegram_msg(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": MY_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.get(url, params=params)
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")

def save_and_check_price(name, price, url): 
    try:
        conn = psycopg2.connect(
            dbname='dns_monitor', user='postgres', 
            password=os.getenv("DB_PASSWORD"), host='localhost', port='5432'
        )
        cur = conn.cursor()

        ext_id = url.split('-')[-1].replace('/', '')

        cur.execute("""
            SELECT ph.price FROM price_history ph
            JOIN products p ON ph.product_id = p.id
            WHERE p.external_id = %s
            ORDER BY ph.created_at DESC LIMIT 1;
        """, (ext_id,))
        
        last_price_row = cur.fetchone()

        cur.execute("""
            INSERT INTO products (external_id, name, url) VALUES (%s, %s, %s)
            ON CONFLICT (external_id) DO NOTHING RETURNING id;
        """, (ext_id, name, url))
        
        res = cur.fetchone()
        product_id = res[0] if res else None
        
        if not product_id:
            cur.execute("SELECT id FROM products WHERE external_id = %s", (ext_id,))
            product_id = cur.fetchone()[0]

        cur.execute("INSERT INTO price_history (product_id, price) VALUES (%s, %s);", (product_id, price))
        conn.commit()

        if last_price_row:
            old_price = float(last_price_row[0])
            if price < old_price:
                diff = old_price - price
                msg = (f"🔥 *НАЙДЕНА СКИДКА!* \n\n"
                       f"📦 *Товар:* {name}\n"
                       f"📉 *Цена упала:* {old_price} ➔ {price} руб.\n"
                       f"💰 *Экономия:* {diff} руб.\n\n"
                       f"🔗 [Открыть в магазине]({url})")
                send_telegram_msg(msg)
                print(f"!!! СКИДКА !!! {name}: {old_price} -> {price}")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Ошибка БД: {e}")

def run_cycle():
    urls = [
        "https://www.citilink.ru/product/smartfon-apple-iphone-16-256gb-a3287-biryuzovyi-2063158/",
        "https://www.citilink.ru/product/smartfon-apple-iphone-17-a3520-256gb-chernyi-3g-4g-1sim-6-3-1206x2622-2143350/?text=iphoen+17+",
        "https://www.citilink.ru/product/smartfon-apple-iphone-17-pro-max-a3526-256gb-temno-sinii-3g-4g-6-9-132-2150264/?text=iphoen+17+pro",
        "https://www.citilink.ru/product/noutbuk-asus-rog-flow-gz302ea-ru045w-ryzen-ai-max-395-32gb-ssd1tb-8060-2153968/"
    ]
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
        headless=True, 
        args=["--proxy-server='direct://'", "--proxy-bypass-list=*"]
        )
        page = browser.new_page() 

        for link in urls:
            try:
                page.goto(link, wait_until="domcontentloaded", timeout=60000)
                time.sleep(3)
                name = page.locator('h1').first.inner_text().strip()
                price_raw = page.locator('[data-meta-price]').first.get_attribute('data-meta-price')
                price = int("".join(filter(str.isdigit, price_raw)))
                
                save_and_check_price(name, price, link)
            except Exception as e:
                print(f"Ошибка на ссылке {link}: {e}")
        
        browser.close()

if __name__ == "__main__":
    while True:
        print(f"\n[{time.strftime('%H:%M:%S')}] Запуск мониторинга...")
        run_cycle()
        print("Проверка завершена. Жду 1 час до следующего запуска...")
        time.sleep(3600) 
