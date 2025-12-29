#!/usr/bin/env python3
"""
Skrypt do lokalnego logowania na Facebook z sesją dla Dockera.
Używa tego samego User-Agent co bot w Dockerze, żeby FB nie zabił sesji.
"""
import asyncio
from playwright.async_api import async_playwright

# Ten sam User-Agent co w Dockerze - KLUCZOWE dla zachowania sesji!
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
FB_DATA_DIR = "fb_data"

async def run():
    print("=" * 60)
    print("🔐 LOKALNY SKRYPT LOGOWANIA DO FACEBOOK")
    print("=" * 60)
    print(f"📁 Folder sesji: {FB_DATA_DIR}")
    print(f"🖥️  User-Agent: {USER_AGENT}")
    print("=" * 60)
    
    async with async_playwright() as p:
        print("\n🌐 Uruchamiam przeglądarkę z sesją dla Dockera...")
        
        # Odpalamy przeglądarkę z folderem sesji i User-Agent Linuxa
        context = await p.chromium.launch_persistent_context(
            FB_DATA_DIR,
            headless=False,  # Z oknem - widzimy co się dzieje
            user_agent=USER_AGENT,  # WAŻNE: Ten sam UA co Docker!
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
        
        print("\n🔗 Ładuję https://m.facebook.com...")
        await page.goto("https://m.facebook.com")
        
        print("\n" + "=" * 60)
        print("⏰ MASZ TERAZ CZAS NA ZALOGOWANIE SIĘ!")
        print("=" * 60)
        print("1. Kliknij 'Akceptuj wszystkie' lub 'Zezwól na wszystkie pliki cookie'")
        print("2. Zaloguj się swoim emailem i hasłem")
        print("3. Poczekaj aż strona się załaduje")
        print("4. Zamknij przeglądarkę (lub poczekaj 3 minuty)")
        print("=" * 60)
        print("\n⏳ Czekam 3 minuty (180 sekund)...\n")
        
        # Czekaj 3 minuty na ręczne logowanie
        await asyncio.sleep(180)
        
        print("\n✅ Czas minął! Zamykam przeglądarkę...")
        await context.close()
        
        print("\n" + "=" * 60)
        print("✅ SESJA ZAPISANA!")
        print("=" * 60)
        print(f"📁 Sesja zapisana w folderze: {FB_DATA_DIR}")
        print("🐳 Docker użyje tej sesji automatycznie")
        print("=" * 60)
        print("\n🚀 Możesz teraz uruchomić bota w Dockerze:")
        print("   docker-compose restart")
        print("   (na Discordzie: !start)")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run())
