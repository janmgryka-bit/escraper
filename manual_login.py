import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        # Odpalamy przeglądarkę z Twoim folderem sesji
        context = await p.chromium.launch_persistent_context(
            'fb_data',
            headless=False,  # CHCEMY TO WIDZIEĆ
            args=['--remote-debugging-port=9222', '--remote-debugging-address=0.0.0.0']
        )
        page = await context.new_page()
        await page.goto("https://m.facebook.com")
        print("!!! MASZ 2 MINUTY NA ZALOGOWANIE SIĘ W TEJ PRZEGLĄDARCE !!!")
        await asyncio.sleep(120)  # Czeka 2 minuty
        await context.close()

asyncio.run(run())
