import asyncio
import random
from datetime import datetime

import discord
from playwright.async_api import async_playwright

from utils.config import DISCORD_TOKEN, CHANNEL_ID, MAX_BUDGET, USER_AGENT, FB_DATA_DIR
from utils.database import Database
from scrapers.olx_scraper import OLXScraper
from scrapers.fb_scraper import FacebookScraper

intents = discord.Intents.default()
bot = discord.Client(intents=intents)

db = Database()
olx_scraper = OLXScraper(MAX_BUDGET, db)
fb_scraper = FacebookScraper()

async def main_loop():
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("❌ BŁĄD: Nie znaleziono kanału Discord! Sprawdź CHANNEL_ID.")
        return
        
    await channel.send(f"🚀 **Janek Hunter v5.3 START!** (Refactored & Improved)")

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            FB_DATA_DIR, 
            headless=True,
            user_agent=USER_AGENT
        )
        
        while True:
            try:
                await fb_scraper.check_notifications(context, channel)
                await olx_scraper.scrape(context, channel)
            except Exception as e:
                print(f"❌ Main loop error: {e}")
                await channel.send(f"⚠️ Błąd w głównej pętli: {str(e)[:100]}")
            
            wait_time = random.randint(120, 240)
            print(f"💤 Czekam {wait_time}s...")
            await asyncio.sleep(wait_time)

@bot.event
async def on_ready():
    print(f"✅ Bot zalogowany jako {bot.user}")
    bot.loop.create_task(main_loop())

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
