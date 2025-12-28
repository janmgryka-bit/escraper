import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        # Tworzy folder na dane sesji
        context = await p.chromium.launch_persistent_context(
            'fb_data', 
            headless=False, # Widzisz okno
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await page.goto("https://www.facebook.com")
        
        print("Czekam na Twoje logowanie... Zaloguj się ręcznie w oknie przeglądarki.")
        print("Gdy zobaczysz stronę główną, wróć tutaj i naciśnij Enter, aby zapisać sesję.")
        
        input("Naciśnij ENTER po poprawnym zalogowaniu...")
        await context.close()
        print("Sesja zapisana w folderze 'fb_data'!")

asyncio.run(run())