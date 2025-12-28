import asyncio
import random
from datetime import datetime

import discord
from playwright.async_api import async_playwright

from utils.config import DISCORD_TOKEN, CHANNEL_ID, MAX_BUDGET, USER_AGENT, FB_DATA_DIR
from utils.database import Database
from utils.logger import setup_logger
from scrapers.olx_scraper import OLXScraper
from scrapers.fb_scraper import FacebookScraper

logger = setup_logger()

intents = discord.Intents.default()
bot = discord.Client(intents=intents)

db = Database()
olx_scraper = OLXScraper(MAX_BUDGET, db)
fb_scraper = FacebookScraper(db)

async def main_loop():
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        logger.error("❌ Nie znaleziono kanału Discord! Sprawdź CHANNEL_ID.")
        print("❌ BŁĄD: Nie znaleziono kanału Discord! Sprawdź CHANNEL_ID.")
        return
    
    logger.info(f"✅ Połączono z kanałem Discord: {channel.name}")
    await channel.send(f"🚀 **Janek Hunter v5.3 START!** (Refactored & Improved)")

    async with async_playwright() as p:
        logger.info("🌐 Uruchamianie przeglądarki Chromium...")
        context = await p.chromium.launch_persistent_context(
            FB_DATA_DIR, 
            headless=True,
            user_agent=USER_AGENT
        )
        logger.info("✅ Przeglądarka gotowa")
        
        cycle = 0
        while True:
            cycle += 1
            logger.info(f"\n{'='*60}")
            logger.info(f"🔄 CYKL #{cycle} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"{'='*60}")
            
            try:
                await fb_scraper.check_notifications(context, channel)
                await olx_scraper.scrape(context, channel)
                logger.info(f"✅ Cykl #{cycle} zakończony pomyślnie")
            except Exception as e:
                logger.error(f"⚠️ Błąd w głównej pętli (cykl #{cycle}): {e}")
                print(f"⚠️ Błąd w głównej pętli: {str(e)[:100]}")
                await channel.send(f"⚠️ Błąd w głównej pętli: {str(e)[:100]}")
            
            wait_time = random.randint(120, 240)
            logger.info(f"💤 Czekam {wait_time}s do następnego cyklu...")
            print(f"💤 Czekam {wait_time}s...")
            await asyncio.sleep(wait_time)

@bot.event
async def on_ready():
    logger.info(f"✅ Bot Discord zalogowany jako {bot.user}")
    logger.info(f"📊 Konfiguracja: MAX_BUDGET={MAX_BUDGET}zł, CHANNEL_ID={CHANNEL_ID}")
    print(f"✅ Bot zalogowany jako {bot.user}")
    bot.loop.create_task(main_loop())

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
