import os
import sqlite3
import asyncio
import random
from datetime import datetime
from dotenv import load_dotenv

import discord
from playwright.async_api import async_playwright

# --- KONFIGURACJA ---
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 1454149554911051961
MAX_BUDGET = 500 

def init_db():
    conn = sqlite3.connect('hunter_final.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS offers 
                   (url TEXT PRIMARY KEY, title TEXT, price TEXT, date_added TEXT)''')
    conn.commit()
    conn.close()

intents = discord.Intents.default()
bot = discord.Client(intents=intents)

async def check_fb_notifications(context, channel):
    page = await context.new_page()
    try:
        print(f"🔔 [{datetime.now().strftime('%H:%M')}] Sprawdzam dzwoneczek FB...")
        await page.goto("https://www.facebook.com/notifications", timeout=60000)
        await asyncio.sleep(5)
        
        notif_locator = page.locator('div[role="gridcell"]').filter(has_text="post")
        count = await notif_locator.count()
        
        for i in range(min(count, 3)):
            notif = notif_locator.nth(i)
            text = await notif.inner_text()
            
            if "iphone" in text.lower():
                print(f"🎯 FB: Trafienie! Klikam...")
                await notif.click()
                await asyncio.sleep(5)
                
                embed = discord.Embed(
                    title="🔵 NOWY POST NA FB (Sprawdź dzwoneczek)", 
                    url="https://www.facebook.com/notifications", 
                    color=discord.Color.blue()
                )
                embed.description = f"Treść powiadomienia: {text[:200]}..."
                await channel.send(embed=embed)
                print("   ✅ Wysłano powiadomienie FB")
                
                await page.goto("https://www.facebook.com/notifications")
                await asyncio.sleep(2)
    except Exception as e: 
        print(f"❌ FB Error: {e}")
    finally: 
        await page.close()

async def scrape_olx(context, channel):
    page = await context.new_page()
    # Blokujemy obrazki totalnie - strona śmiga błyskawicznie
    await page.route("**/*.{png,jpg,jpeg,webp,gif,svg}", lambda route: route.abort())
    
    try:
        print(f"📡 [{datetime.now().strftime('%H:%M')}] Skanowanie OLX (Top 25)...")
        
        # Wejście na stronę
        await page.goto(
            "https://www.olx.pl/elektronika/telefony/smartfony-telefony-komorkowe/warszawa/q-iphone/?search%5Bdist%5D=50&search%5Bprivate_business%5D=private&search%5Border%5D=created_at:desc&search%5Bfilter_enum_state%5D%5B0%5D=damaged&search%5Bfilter_enum_state%5D%5B1%5D=used", 
            wait_until="commit", 
            timeout=30000
        )

        await page.wait_for_selector('div[data-cy="l-card"]', timeout=15000)
        offers = await page.locator('div[data-cy="l-card"]').all()
        conn = sqlite3.connect('hunter_final.db')
        
        for offer in offers[:25]:
            try:
                # Pobranie ceny
                price_el = offer.locator('p[data-testid="ad-price"]')
                if await price_el.count() == 0: continue
                price_text = await price_el.inner_text()
                price_val = int(''.join(filter(str.isdigit, price_text.split(',')[0])))
                
                if price_val > MAX_BUDGET:
                    continue
                
                # Pobranie URL
                link_el = offer.locator('a').first
                raw_href = await link_el.get_attribute('href')
                url = ("https://www.olx.pl" + raw_href if "olx.pl" not in raw_href else raw_href).split('#')[0]
                
                # Sprawdzenie bazy
                if conn.execute("SELECT url FROM offers WHERE url=?", (url,)).fetchone():
                    continue

                # Pobranie tytułu
                full_text = await offer.inner_text()
                title = full_text.split('\n')[0].lower()
                
                # Szybki filtr starych modeli
                if any(x in title for x in ['iphone 7', 'iphone 8', 'iphone x', 'se 2016']):
                    print(f"   🚫 Pomijam stary model: {title[:20]}")
                    continue

                print(f"🎯 OKAZJA! Próba wysyłki: {title[:30]} | {price_val}zł")
                
                # --- WYSYŁKA NA DISCORD (BEZ AI - PEWNIAK) ---
                embed = discord.Embed(
                    title=f"📱 {title.upper()}", 
                    url=url, 
                    color=discord.Color.green()
                )
                embed.add_field(name="Cena", value=f"**{price_val} zł**", inline=True)
                embed.add_field(name="Status", value="Nowe ogłoszenie!", inline=True)
                embed.set_footer(text="Janek Hunter v5.2 - Auto-Send")

                try:
                    await channel.send(embed=embed)
                    print(f"   ✅ SUKCES! Wysłano na Discord.")
                except Exception as de:
                    print(f"   ❌ BŁĄD DISCORDA: {de}")

                # Zapis do bazy
                conn.execute("INSERT INTO offers (url, title, price, date_added) VALUES (?, ?, ?, ?)", 
                             (url, title, str(price_val), datetime.now().isoformat()))
                conn.commit()
                
            except Exception as e:
                continue
        conn.close()
    except Exception as e: 
        print(f"❌ OLX Global Error: {e}")
    finally: 
        if not page.is_closed(): await page.close()

async def main_loop():
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("❌ BŁĄD: Nie znaleziono kanału Discord! Sprawdź CHANNEL_ID.")
        return
        
    await channel.send(f"🚀 **Janek Hunter v5.2 START!** (Bez AI, Bez zdjęć - 100% skuteczności)")

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            'fb_data', 
            headless=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        
        while True:
            await check_fb_notifications(context, channel)
            await scrape_olx(context, channel)
            
            wait_time = random.randint(120, 240)
            print(f"💤 Czekam {wait_time}s...")
            await asyncio.sleep(wait_time)

@bot.event
async def on_ready():
    print(f"✅ Bot zalogowany jako {bot.user}")
    init_db()
    bot.loop.create_task(main_loop())

bot.run(DISCORD_TOKEN)