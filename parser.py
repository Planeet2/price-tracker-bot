from playwright.sync_api import sync_playwright
import time

def get_citilink_data(url='https://citilink.ru'):
    with sync_playwright() as p:
        
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        print(f"Пробую Ситилинк: {url}")
        
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(5) 

            product_name = page.locator('h1').inner_text(timeout=10000).strip()
            
            
            price_text = page.locator('[data-meta-price]').get_attribute('data-meta-price')
            
            print(f"\nУСПЕХ!")
            print(f"Товар: {product_name}")
            print(f"Цена: {price_text}")
            
            return product_name, price_text

        except Exception as e:
            print(f"\nОшибка: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    get_citilink_data()
