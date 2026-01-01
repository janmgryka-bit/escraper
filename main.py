import asyncio
import random
from datetime import datetime, timedelta
import os
import discord
from discord.ext import commands
from playwright.async_api import async_playwright
from dotenv import load_dotenv
import logging
import yaml

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
    "playwright_context": None,
    "current_group_index": 0  # Indeks aktualnej grupy do rotacji
}

async def refresh_groups_if_needed():
    """Automatyczne odświeżanie listy grup co 12 godzin"""
    try:
        with open('config.yaml', 'r') as f:
            config_data = yaml.safe_load(f)
        
        fb_config = config_data.get('facebook', {})
        last_refresh = fb_config.get('last_groups_refresh')
        refresh_hours = fb_config.get('refresh_groups_hours', 12)
        
        now = datetime.now()
        should_refresh = False
        
        if not last_refresh:
            should_refresh = True
            logger.info("🔄 [GROUPS] Nigdy nie odświeżano grup - odświeżam...")
        else:
            if isinstance(last_refresh, str):
                last_refresh = datetime.fromisoformat(last_refresh)
            time_diff = now - last_refresh
            if time_diff.total_seconds() > refresh_hours * 3600:
                should_refresh = True
                logger.info(f"🔄 [GROUPS] Minęło {refresh_hours}h - odświeżam grupy...")
        
        if should_refresh:
            from extract_groups import extract_my_groups
            groups_count = await extract_my_groups()
            
            # Aktualizuj timestamp w configu
            config_data['facebook']['last_groups_refresh'] = now.isoformat()
            with open('config.yaml', 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False)
            
            logger.info(f"✅ [GROUPS] Odświeżono {groups_count} grup")
            
    except Exception as e:
        logger.error(f"❌ [GROUPS] Błąd odświeżania grup: {e}")

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
            # BROWSER REWIND PRZED cyklem - tylko po pierwszym cyklu
            if cycle > 0:
                logger.info("🔄 BROWSER REWIND - zamykam stary context...")
                try:
                    old_context = bot_state.get("playwright_context")
                    old_browser = bot_state.get("playwright_browser")
                    
                    if old_context:
                        await old_context.close()
                    if old_browser:
                        await old_browser.close()
                        
                    logger.info("✅ Stary browser zamknięty")
                    
                    # Otwórz nowy browser
                    from playwright.async_api import async_playwright
                    import json
                    import os
                    
                    p = await async_playwright().start()
                    new_browser = await p.chromium.launch(
                        headless=True,
                        args=[
                            '--no-sandbox',
                            '--disable-setuid-sandbox',
                            '--disable-dev-shm-usage',
                            '--disable-gpu',
                            '--disable-software-rasterizer',
                            '--disable-extensions',
                            '--disable-web-security'
                        ]
                    )
                    
                    new_context = await new_browser.new_context(user_agent=USER_AGENT)
                    
                    # Wczytaj ciasteczka
                    if os.path.exists('fb_cookies.json'):
                        with open('fb_cookies.json', 'r') as f:
                            cookies = json.load(f)
                        await new_context.add_cookies(cookies)
                    
                    bot_state["playwright_context"] = new_context
                    bot_state["playwright_browser"] = new_browser
                    logger.info("✅ Nowy browser context otwarty")
                    
                    # CRITICAL: Poczekaj na pełne zainicjowanie nowego context
                    await asyncio.sleep(1)
                    logger.info("⏱️ [BROWSER] Nowy context w pełni zainicjowany")
                    
                except Exception as e:
                    logger.error(f"❌ Błąd podczas browser rewind: {e}")
            
            # CRITICAL: Pobierz FRESH context po browser rewind
            context = bot_state.get("playwright_context")
            if not context:
                logger.error("❌ [BROWSER] Brak dostępnego context - pomijam cykl")
                await asyncio.sleep(30)
                continue
            
            # Automatyczne odświeżanie grup co 12 godzin
            await refresh_groups_if_needed()
            
            # Przeładuj config co 10 cykli (auto-refresh)
            if cycle % 10 == 0:
                logger.info("🔄 Przeładuję konfigurację...")
                config.reload()
            
            # ASYNC ISOLATION - każdy scraper w osobnym try...except
            fb_success = True
            olx_success = True
            allegro_success = True
            
            # Facebook - rotacja grup (jedna grupa na cykl)
            try:
                await fb_scraper.scan_group_feed(context, channel)
                logger.info("✅ [FB] Scraper zakończony sukcesem")
                # ASYNC SLEEP - pozwól Discordowi odetchnąć
                await asyncio.sleep(0.1)
            except Exception as e:
                fb_success = False
                logger.error(f"❌ [FB] Błąd scrapera: {e}")
                import traceback
                logger.error(f"❌ [FB] Traceback: {traceback.format_exc()}")
                # ASYNC SLEEP - pozwól Discordowi odetchnąć
                await asyncio.sleep(0.1)
            
            # OLX scraper
            try:
                await olx_scraper.scrape(context, channel)
                logger.info("✅ [OLX] Scraper zakończony sukcesem")
                # ASYNC SLEEP - pozwól Discordowi odetchnąć
                await asyncio.sleep(0.1)
            except Exception as e:
                olx_success = False
                logger.error(f"❌ [OLX] Błąd scrapera: {e}")
                import traceback
                logger.error(f"❌ [OLX] Traceback: {traceback.format_exc()}")
                # ASYNC SLEEP - pozwól Discordowi odetchnąć
                await asyncio.sleep(0.1)
            
            # Allegro Lokalnie (jeśli włączone)
            allegro_config = config.config.get('sources', {}).get('allegro_lokalnie', {})
            if allegro_config.get('enabled', False):
                try:
                    await allegro_scraper.scrape(context, channel)
                    logger.info("✅ [Allegro] Scraper zakończony sukcesem")
                    # ASYNC SLEEP - pozwól Discordowi odetchnąć
                    await asyncio.sleep(0.1)
                except Exception as e:
                    allegro_success = False
                    logger.error(f"❌ [Allegro] Błąd scrapera: {e}")
                    import traceback
                    logger.error(f"❌ [Allegro] Traceback: {traceback.format_exc()}")
                    # ASYNC SLEEP - pozwól Discordowi odetchnąć
                    await asyncio.sleep(0.1)
            
            # Podsumowanie cyklu
            status_parts = []
            if fb_success: status_parts.append("FB✅")
            else: status_parts.append("FB❌")
            if olx_success: status_parts.append("OLX✅")
            else: status_parts.append("OLX❌")
            if allegro_config.get('enabled', False):
                if allegro_success: status_parts.append("Allegro✅")
                else: status_parts.append("Allegro❌")
            
            logger.info(f"✅ Cykl #{cycle} zakończony: {', '.join(status_parts)}")
        
        except Exception as e:
            logger.error(f"⚠️ Błąd w głównej pętli (cykl #{cycle}): {e}")
            await channel.send(f"⚠️ Błąd w głównej pętli: {str(e)[:100]}")
        
        # DOCKER RESOURCE CHECK - sprawdź pamięć RAM
        try:
            import psutil
            memory = psutil.virtual_memory()
            logger.info(f"💾 DOCKER RESOURCE CHECK - RAM: {memory.percent}% użyte ({memory.available//1024//1024}MB wolne)")
        except Exception as e:
            logger.debug(f"Nie można sprawdzić pamięci: {e}")
        
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
    
    # Inicjalizuj Playwright context przy starcie bota (cookie injection)
    logger.info("🌐 Inicjalizacja Playwright...")
    print("DEBUG: Inicjalizuję context z cookie injection...")
    try:
        from playwright.async_api import async_playwright
        import json
        import os
        
        p = await async_playwright().start()
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-software-rasterizer',
                '--disable-extensions',
                '--disable-web-security'  # HEADLESS CHECK - łatwiejsze ładowanie dynamicznych treści FB
            ]
        )
        
        # Stwórz nowy context z User-Agent
        context = await browser.new_context(user_agent=USER_AGENT)
        
        # Wczytaj i wstrzyknij ciasteczka
        if os.path.exists('fb_cookies.json'):
            print("DEBUG: Wczytuję ciasteczka z fb_cookies.json...")
            with open('fb_cookies.json', 'r') as f:
                cookies = json.load(f)
            await context.add_cookies(cookies)
            print(f"DEBUG: Wstrzyknięto {len(cookies)} ciasteczek")
        else:
            print("DEBUG: Brak pliku fb_cookies.json - kontynuuję bez ciasteczek")
        
        bot_state["playwright_context"] = context
        bot_state["playwright_browser"] = browser
        logger.info("✅ Playwright context gotowy (cookie injection)")
        print("DEBUG: Context z cookie injection gotowy")
    except Exception as e:
        logger.error(f"❌ Błąd inicjalizacji Playwright: {e}")
        print(f"DEBUG: Błąd inicjalizacji context: {e}")
    
    logger.info(f"⏸️  Bot czeka na komendę !start")

if __name__ == "__main__":
    logger.info("🚀 Uruchamianie Janek Hunter v6.0...")
    logger.info("📝 Konfiguracja: config.yaml")
    logger.info("🔧 System: Advanced Config + AI + Smart Matching")
    bot.run(DISCORD_TOKEN)
