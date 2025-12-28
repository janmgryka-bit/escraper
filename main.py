import asyncio
import random
from datetime import datetime

import discord
from playwright.async_api import async_playwright

from utils.config import DISCORD_TOKEN, CHANNEL_ID, USER_AGENT, FB_DATA_DIR
from utils.database import Database
from utils.logger import setup_logger
from utils.config_loader import ConfigLoader
from utils.profitability import ProfitabilityCalculator
from utils.ai_analyzer import AIAnalyzer
from scrapers.olx_scraper import OLXScraper
from scrapers.fb_scraper import FacebookScraper

logger = setup_logger()

# Inicjalizacja nowego systemu
config = ConfigLoader('config.yaml')
db = Database()
profit_calc = ProfitabilityCalculator(config)
ai_analyzer = AIAnalyzer(config)

# Inicjalizacja scraperów z nowym systemem
olx_scraper = OLXScraper(db, config, profit_calc, ai_analyzer)
fb_scraper = FacebookScraper(db, config, profit_calc, ai_analyzer)

intents = discord.Intents.default()
bot = discord.Client(intents=intents)

async def main_loop():
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        logger.error("❌ Nie znaleziono kanału Discord! Sprawdź CHANNEL_ID.")
        return
    
    logger.info(f"✅ Połączono z kanałem Discord: {channel.name}")
    
    # Pokaż konfigurację
    enabled_models = config.get_enabled_models()
    enabled_conditions = config.get_enabled_conditions()
    logger.info(f"📱 Modele: {', '.join(enabled_models[:5])}... ({len(enabled_models)} total)")
    logger.info(f"📊 Stany: {', '.join(enabled_conditions)}")
    logger.info(f"🤖 AI: {'✅ Włączone' if ai_analyzer.enabled else '❌ Wyłączone'}")
    logger.info(f"💡 Smart Matching: {'✅ Włączone' if config.is_smart_matching_enabled() else '❌ Wyłączone'}")
    
    await channel.send(
        f"🚀 **Janek Hunter v6.0 START!**\n"
        f"📱 Modele: {len(enabled_models)}\n"
        f"📊 Stany: {', '.join(enabled_conditions)}\n"
        f"🤖 AI: {'✅' if ai_analyzer.enabled else '❌'}\n"
        f"💡 Smart Matching: {'✅' if config.is_smart_matching_enabled() else '❌'}"
    )

    async with async_playwright() as p:
        logger.info("🌐 Uruchamianie przeglądarki Chromium...")
        try:
            # Użyj channel=chromium z executable_path dla systemowej przeglądarki
            context = await p.chromium.launch_persistent_context(
                'fb_data',
                headless=True,
                user_agent=USER_AGENT,
                channel='chromium',
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-software-rasterizer'
                ]
            )
            logger.info("✅ Przeglądarka gotowa (system Chromium)")
        except Exception as e:
            logger.error(f"❌ Błąd uruchamiania przeglądarki: {e}")
            logger.error("💡 Próbuję bez channel...")
            # Fallback - bez channel
            try:
                context = await p.chromium.launch_persistent_context(
                    'fb_data',
                    headless=True,
                    user_agent=USER_AGENT,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu'
                    ]
                )
                logger.info("✅ Przeglądarka gotowa (Playwright Chromium)")
            except Exception as e2:
                logger.error(f"❌ Błąd: {e2}")
                raise
        
        cycle = 0
        while True:
            cycle += 1
            logger.info(f"\n{'='*60}")
            logger.info(f"🔄 CYKL #{cycle} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"{'='*60}")
            
            try:
                # Przeładuj config co 10 cykli (auto-refresh)
                if cycle % 10 == 0:
                    logger.info("🔄 Przeładowuję konfigurację...")
                    config.reload()
                
                await fb_scraper.check_notifications(context, channel)
                await olx_scraper.scrape(context, channel)
                logger.info(f"✅ Cykl #{cycle} zakończony pomyślnie")
            except Exception as e:
                logger.error(f"⚠️ Błąd w głównej pętli (cykl #{cycle}): {e}")
                await channel.send(f"⚠️ Błąd w głównej pętli: {str(e)[:100]}")
            
            # Pobierz interwał z konfiguracji
            min_wait, max_wait = config.get_check_interval()
            wait_time = random.randint(min_wait, max_wait)
            logger.info(f"💤 Czekam {wait_time}s do następnego cyklu...")
            await asyncio.sleep(wait_time)

@bot.event
async def on_ready():
    logger.info(f"✅ Bot Discord zalogowany jako {bot.user}")
    logger.info(f"📊 Konfiguracja załadowana z: config.yaml")
    bot.loop.create_task(main_loop())

if __name__ == "__main__":
    logger.info("🚀 Uruchamianie Janek Hunter v6.0...")
    logger.info("📝 Konfiguracja: config.yaml")
    logger.info("🔧 System: Advanced Config + AI + Smart Matching")
    bot.run(DISCORD_TOKEN)
