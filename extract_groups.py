import asyncio
import yaml
from playwright.async_api import async_playwright
import json
import logging

# Ustawienie loggera
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def extract_my_groups():
    """Wyciąga listę grup użytkownika i zapisuje do config.yaml"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            # Ładujemy Twoje ciasteczka, żeby być zalogowanym
            context = await browser.new_context()
            with open('fb_cookies.json', 'r') as f:
                cookies = json.load(f)
                await context.add_cookies(cookies)
            
            page = await context.new_page()
            logger.info("🔗 Wchodzę na listę Twoich grup...")
            await page.goto("https://m.facebook.com/groups/?category=membership", wait_until="networkidle")
            
            # Przewijamy trochę, żeby załadować listę
            for _ in range(3):
                await page.mouse.wheel(0, 2000)
                await asyncio.sleep(2)

            # Szukamy linków do grup
            links = await page.query_selector_all('a[href*="/groups/"]')
            group_urls = set()
            
            for link in links:
                href = await link.get_attribute('href')
                if "/groups/" in href and "category" not in href:
                    # Czyszczenie linku do czystego ID/nazwy
                    clean_url = href.split('?')[0].split('&')[0]
                    if not clean_url.startswith('http'):
                        clean_url = "https://www.facebook.com" + clean_url
                    group_urls.add(clean_url)

            logger.info(f"✅ Znaleziono {len(group_urls)} grup.")

            # Aktualizacja config.yaml
            with open('config.yaml', 'r') as f:
                config = yaml.safe_load(f)

            config['facebook']['priority_groups'] = list(group_urls)

            with open('config.yaml', 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            logger.info("💾 Grupy zostały zapisane do config.yaml")
            await browser.close()
            return len(group_urls)
            
    except Exception as e:
        logger.error(f"❌ Błąd podczas wyciągania grup: {e}")
        return 0

if __name__ == "__main__":
    asyncio.run(extract_my_groups())
