import re
import time
from dataclasses import dataclass
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from app.config import settings


@dataclass(frozen=True)
class ProductData:
    external_id: str
    name: str
    price: int
    url: str


def extract_external_id(url: str) -> str:
    path = urlparse(url).path.strip("/")
    match = re.search(r"-(\d+)/?$", path)
    if match:
        return match.group(1)
    return path.split("/")[-1]


def scrape_product(url: str) -> ProductData:
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=settings.headless,
            args=["--proxy-server=direct://", "--proxy-bypass-list=*"],
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(3)

            name = page.locator("h1").first.inner_text(timeout=15000).strip()
            price_raw = page.locator("[data-meta-price]").first.get_attribute(
                "data-meta-price", timeout=15000
            )

            if not price_raw:
                raise ValueError("Не удалось найти цену на странице")

            price = int("".join(filter(str.isdigit, price_raw)))
            return ProductData(
                external_id=extract_external_id(url),
                name=name,
                price=price,
                url=url,
            )
        except PlaywrightTimeoutError as exc:
            raise RuntimeError(f"Страница слишком долго загружалась: {url}") from exc
        finally:
            browser.close()
