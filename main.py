import psycopg2
from playwright.sync_api import sync_playwright
import time

def save_to_database(name, price, url):
    try:
        conn = psycopg2.connect(
            dbname='dns_monitor',
            user = 'postgres',
            password = '1089',
            host = 'localhost',
            port = '5432'
        )
        cur = conn.cursor()

        ext_id = url.split('-')[-1].replace('/', '')

        cur.execute("""
                    INSERT INTO products(external_id, name, url)
                    VALUES(%s, %s, %s)
                    ON CONFLICT (external_id) DO NOTHING
                    RETURNING id;
                    """, (ext_id, name, url))
        
        result = cur.fetchone()

        if result:
            product_id = result[0]
        else:
            cur.execute("SELECT id FROM products WHERE external_id = %s", (ext_id,))
            product_id = cur.fetchone()[0]
        cur.execute("""
                    INSERT INTO price_history(product_id, price)
                    VALUES(%s, %s);
                    """, (product_id, price))
        conn.commit()
        print("Данные успешно сохранены в базу данных.")
    except Exception as e:
        print(f"Ошибка при сохранении данных: {e}")
    
def start_parsing(url): 
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded")
        time.sleep(5)
        
        name = page.locator('h1').first.inner_text().strip()
       
        price_raw = page.locator('[data-meta-price]').first.get_attribute('data-meta-price')
        clean_price = "".join(filter(str.isdigit, price_raw))

        
        save_to_database(name, int(clean_price), url)
        browser.close()

if __name__ == "__main__":
    urls = [
        "https://www.citilink.ru/product/smartfon-apple-iphone-16-256gb-a3287-biryuzovyi-2063158/",
        "https://www.citilink.ru/product/smartfon-apple-iphone-17-a3520-256gb-chernyi-3g-4g-1sim-6-3-1206x2622-2143350/?text=iphoen+17+",
        "https://www.citilink.ru/product/smartfon-apple-iphone-17-pro-max-a3526-256gb-temno-sinii-3g-4g-6-9-132-2150264/?text=iphoen+17+pro",
        "https://www.citilink.ru/product/noutbuk-asus-rog-flow-gz302ea-ru045w-ryzen-ai-max-395-32gb-ssd1tb-8060-2153968/"
    ]
    for index, link in enumerate(urls, start=1):
        print(f"\n[{index}/{len(urls)}] Работаю с товаром...")
        try:
            start_parsing(link)
            time.sleep(3) 
        except Exception as e:
            print(f"❌ Ошибка при обработке {link}: {e}")
            continue 

    print("\n✅ Все товары из списка обработаны!")


                    