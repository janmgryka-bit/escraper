#!/usr/bin/env python3
"""
Skrypt do wyciągnięcia ciasteczek Facebook z lokalnej przeglądarki.
Zapisuje je do fb_cookies.json do wstrzyknięcia w Dockerze.
"""
import asyncio
import json
from playwright.async_api import async_playwright

# Ten sam User-Agent co w Dockerze - KLUCZOWE dla zachowania sesji!
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

async def run():
    print("=" * 60)
    print("🍪 EKSPORTOWANIE CIASTECZEK FACEBOOK")
    print("=" * 60)
    print(f"🖥️  User-Agent: {USER_AGENT}")
    print("=" * 60)
    
    async with async_playwright() as p:
        print("\n🌐 Uruchamiam przeglądarkę...")
        
        # Odpalamy przeglądarkę z User-Agent Linuxa
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(user_agent=USER_AGENT)
        
        page = await context.new_page()
        
        print("\n🔗 Ładuję https://m.facebook.com...")
        await page.goto("https://m.facebook.com")
        
        print("\n" + "=" * 60)
        print("⏰ ZALOGUJ SIĘ TERAZ!")
        print("=" * 60)
        print("1. Kliknij 'Akceptuj wszystkie' lub 'Zezwól na wszystkie pliki cookie'")
        print("2. Zaloguj się swoim emailem i hasłem")
        print("3. Poczekaj aż strona się załaduje (zobaczysz swój profil)")
        print("4. Wróć do terminala i naciśnij ENTER")
        print("=" * 60)
        print("\n⏳ Czekam na ENTER...")
        
        # Czekaj na ENTER od użytkownika
        input()
        
        print("\n🍪 Wyciągam ciasteczka...")
        
        # Wyciągnij wszystkie ciasteczka
        cookies = await context.cookies()
        
        print(f"✅ Znaleziono {len(cookies)} ciasteczek")
        
        # Zapisz ciasteczka do pliku JSON
        with open('fb_cookies.json', 'w') as f:
            json.dump(cookies, f, indent=2)
        
        print("\n" + "=" * 60)
        print("✅ CIASTECZKA ZAPISANE!")
        print("=" * 60)
        print(f"📁 Plik: fb_cookies.json")
        print(f"🍪 Liczba ciasteczek: {len(cookies)}")
        print("🐳 Docker użyje tych ciasteczek do logowania")
        print("=" * 60)
        print("\n🚀 Możesz teraz uruchomić bota w Dockerze:")
        print("   docker-compose restart")
        print("   (na Discordzie: !start)")
        print("=" * 60)
        
        # Pokaż kilka przykładowych ciasteczek
        print("\n📋 Przykładowe ciasteczka:")
        for i, cookie in enumerate(cookies[:5]):
            print(f"  {i+1}. {cookie['name']} = {cookie['value'][:30]}...")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
