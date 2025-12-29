import asyncio
import os
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

# Identyczny User-Agent jak w main.py
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
FB_DATA_DIR = 'fb_data'

async def run():
    fb_email = os.getenv('FB_EMAIL')
    fb_password = os.getenv('FB_PASSWORD')
    
    if not fb_email or not fb_password:
        print("❌ Błąd: Brak FB_EMAIL lub FB_PASSWORD w pliku .env")
        return
    
    print("🔐 Rozpoczynam logowanie do Facebooka w trybie headless...")
    print(f"📧 Email: {fb_email}")
    
    async with async_playwright() as p:
        # Tworzy folder na dane sesji z identycznym User-Agent jak w main.py
        context = await p.chromium.launch_persistent_context(
            FB_DATA_DIR,
            headless=True,  # Bez okna - działa w Dockerze
            user_agent=USER_AGENT,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-software-rasterizer',
                '--disable-extensions'
            ]
        )
        
        page = await context.new_page()
        
        try:
            print("🌐 Ładowanie m.facebook.com...")
            await page.goto("https://m.facebook.com", timeout=30000)
            await asyncio.sleep(2)
            
            # Sprawdź czy już zalogowany
            if await page.locator('input[name="email"]').count() == 0:
                print("✅ Już zalogowany! Sesja aktywna.")
                await context.close()
                return
            
            print("📝 Wpisuję email...")
            await page.fill('input[name="email"]', fb_email)
            await asyncio.sleep(1)
            
            print("🔑 Wpisuję hasło...")
            await page.fill('input[name="pass"]', fb_password)
            await asyncio.sleep(1)
            
            print("🚀 Klikam 'Zaloguj się'...")
            await page.click('button[name="login"], input[name="login"]')
            
            print("⏳ Czekam 10 sekund na załadowanie...")
            await asyncio.sleep(10)
            
            # Sprawdź czy logowanie się powiodło
            if await page.locator('input[name="email"]').count() > 0:
                print("❌ Logowanie nie powiodło się - nadal widać formularz logowania")
                await page.screenshot(path='fb_login_error.png')
                print("📸 Screenshot zapisany jako fb_login_error.png")
            else:
                print("✅ Logowanie pomyślne!")
                await page.screenshot(path='fb_login_success.png')
                print("📸 Screenshot zapisany jako fb_login_success.png")
            
            await context.close()
            print(f"💾 Sesja zapisana w folderze '{FB_DATA_DIR}'!")
            
        except Exception as e:
            print(f"❌ Błąd podczas logowania: {e}")
            await page.screenshot(path='fb_login_exception.png')
            print("📸 Screenshot błędu zapisany jako fb_login_exception.png")
            await context.close()

if __name__ == "__main__":
    asyncio.run(run())