import asyncio
import random
from datetime import datetime
import os
import discord
from discord.ext import commands
from playwright.async_api import async_playwright
from dotenv import load_dotenv
import logging

from utils.config import DISCORD_TOKEN, CHANNEL_ID, USER_AGENT, FB_DATA_DIR
from utils.database import Database
from utils.logger import setup_logger
from utils.config_loader import ConfigLoader
from utils.profitability import ProfitabilityCalculator
from utils.ai_analyzer import AIAnalyzer
from scrapers.olx_scraper import OLXScraper
from scrapers.fb_scraper import FacebookScraper
from scrapers.allegro_scraper import AllegroScraper

logger = setup_logger()

# Inicjalizacja nowego systemu
config = ConfigLoader('config.yaml')
db = Database()
profit_calc = ProfitabilityCalculator(config)
ai_analyzer = AIAnalyzer(config)

# Inicjalizacja scraperów z nowym systemem
olx_scraper = OLXScraper(db, config, profit_calc, ai_analyzer)
fb_scraper = FacebookScraper(db, config, profit_calc, ai_analyzer)
allegro_scraper = AllegroScraper(db, config, profit_calc, ai_analyzer)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Bot runtime state
bot_state = {
    "is_running": False,
    "scraper_task": None,
    "playwright_context": None
}

async def main_loop():
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        logger.error("❌ Nie znaleziono kanału Discord! Sprawdź CHANNEL_ID.")
        return
    
    logger.info(f"✅ Połączono z kanałem Discord: {channel.name}")
    
    # Pobierz context z bot_state
    context = bot_state["playwright_context"]
    if not context:
        logger.error("❌ Playwright context nie został zainicjalizowany!")
        return
    
    cycle = 0
    while True:
        cycle += 1
        logger.info(f"\n{'='*60}")
        logger.info(f"🔄 CYKL #{cycle} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"{'='*60}")
        
        # Sprawdź czy bot nadal ma działać
        if not bot_state["is_running"]:
            logger.info("🛑 Bot zatrzymany przez użytkownika")
            break
        
        try:
            # Przeładuj config co 10 cykli (auto-refresh)
            if cycle % 10 == 0:
                logger.info("🔄 Przeładowuję konfigurację...")
                config.reload()
            
            # Facebook notifications
            await fb_scraper.check_notifications(context, channel)
            
            # OLX scraper
            await olx_scraper.scrape(context, channel)
            
            # Allegro Lokalnie (jeśli włączone)
            allegro_config = config.config.get('sources', {}).get('allegro_lokalnie', {})
            if allegro_config.get('enabled', False):
                await allegro_scraper.scrape(context, channel)
            
            logger.info(f"✅ Cykl #{cycle} zakończony pomyślnie")
        except Exception as e:
            logger.error(f"⚠️ Błąd w głównej pętli (cykl #{cycle}): {e}")
            await channel.send(f"⚠️ Błąd w głównej pętli: {str(e)[:100]}")
        
        # Pobierz interwał z konfiguracji
        min_wait, max_wait = config.get_check_interval()
        wait_time = random.randint(min_wait, max_wait)
        logger.info(f"💤 Czekam {wait_time}s do następnego cyklu...")
        await asyncio.sleep(wait_time)

@bot.command(name="set_budget")
async def set_budget_cmd(ctx, budget: int):
    """Zmień maksymalny budżet (np. !set_budget 800)"""
    if budget < 0:
        return await ctx.send("❌ Budżet musi być liczbą dodatnią!")
    
    config.config['general']['max_budget'] = budget
    config.save()
    
    embed = discord.Embed(
        title="💰 Budżet zaktualizowany",
        description=f"Nowy maksymalny budżet: **{budget} zł**",
        color=discord.Color.green()
    )
    
    if not bot_state["is_running"]:
        embed.add_field(
            name="ℹ️ Info",
            value="Bot nie jest uruchomiony. Użyj `!start` aby rozpocząć skanowanie.",
            inline=False
        )
    
    await ctx.send(embed=embed)
    logger.info(f"💰 Budżet zmieniony na {budget} zł przez {ctx.author}")

@bot.command(name="start")
async def start_cmd(ctx):
    """Uruchom skanowanie (np. !start)"""
    if bot_state["is_running"]:
        return await ctx.send("⚠️ Skanowanie już trwa!")
    
    max_budget = config.get_max_budget()
    
    # Przycisk potwierdzenia
    view = discord.ui.View(timeout=60)
    
    async def confirm_callback(interaction):
        await interaction.response.defer()
        bot_state["is_running"] = True
        bot_state["scraper_task"] = bot.loop.create_task(main_loop())
        
        embed = discord.Embed(
            title="🚀 Skanowanie uruchomione!",
            description=f"Budżet: **{max_budget} zł**\nŹródła: OLX, Facebook, Allegro Lokalnie",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed)
        logger.info(f"🚀 Skanowanie uruchomione przez {interaction.user}")
    
    async def cancel_callback(interaction):
        await interaction.response.send_message("❌ Anulowano uruchomienie.", ephemeral=True)
    
    confirm_btn = discord.ui.Button(label="✅ TAK, START", style=discord.ButtonStyle.green)
    cancel_btn = discord.ui.Button(label="❌ NIE", style=discord.ButtonStyle.red)
    
    confirm_btn.callback = confirm_callback
    cancel_btn.callback = cancel_callback
    
    view.add_item(confirm_btn)
    view.add_item(cancel_btn)
    
    embed = discord.Embed(
        title="🛰️ Potwierdzenie uruchomienia",
        description=f"Budżet: **{max_budget} zł**\n\nCzy chcesz uruchomić skanowanie?",
        color=discord.Color.blue()
    )
    
    await ctx.send(embed=embed, view=view)

@bot.command(name="stop")
async def stop_cmd(ctx):
    """Zatrzymaj skanowanie (np. !stop)"""
    if not bot_state["is_running"]:
        return await ctx.send("⚠️ Skanowanie nie jest uruchomione!")
    
    bot_state["is_running"] = False
    if bot_state["scraper_task"]:
        bot_state["scraper_task"].cancel()
        bot_state["scraper_task"] = None
    
    embed = discord.Embed(
        title="🛑 Skanowanie zatrzymane",
        description="Bot przestał skanować oferty.",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)
    logger.info(f"🛑 Skanowanie zatrzymane przez {ctx.author}")

@bot.command(name="status")
async def status_cmd(ctx):
    """Sprawdź status bota (np. !status)"""
    max_budget = config.get_max_budget()
    status = "🟢 Uruchomiony" if bot_state["is_running"] else "🔴 Zatrzymany"
    
    embed = discord.Embed(
        title="📊 Status Bota",
        color=discord.Color.green() if bot_state["is_running"] else discord.Color.red()
    )
    embed.add_field(name="Status", value=status, inline=True)
    embed.add_field(name="Budżet", value=f"{max_budget} zł", inline=True)
    embed.add_field(name="Źródła", value="OLX, Facebook, Allegro", inline=False)
    
    await ctx.send(embed=embed)

@bot.event
async def on_ready():
    logger.info(f"✅ Bot Discord zalogowany jako {bot.user}")
    logger.info(f"📊 Konfiguracja załadowana z: config.yaml")
    logger.info(f"💬 Komendy: !start, !stop, !set_budget, !status")
    
    # Inicjalizuj Playwright context przy starcie bota
    logger.info("🌐 Inicjalizacja Playwright...")
    print(f"DEBUG: Próba użycia sesji z folderu {FB_DATA_DIR}...")
    try:
        from playwright.async_api import async_playwright
        p = await async_playwright().start()
        context = await p.chromium.launch_persistent_context(
            FB_DATA_DIR,
            headless=True,
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
        bot_state["playwright_context"] = context
        logger.info("✅ Playwright context gotowy (persistent session)")
        print(f"DEBUG: Sesja z {FB_DATA_DIR} załadowana pomyślnie")
    except Exception as e:
        logger.error(f"❌ Błąd inicjalizacji Playwright: {e}")
        print(f"DEBUG: Błąd ładowania sesji z {FB_DATA_DIR}: {e}")
    
    logger.info(f"⏸️  Bot czeka na komendę !start")

if __name__ == "__main__":
    logger.info("🚀 Uruchamianie Janek Hunter v6.0...")
    logger.info("📝 Konfiguracja: config.yaml")
    logger.info("🔧 System: Advanced Config + AI + Smart Matching")
    bot.run(DISCORD_TOKEN)
