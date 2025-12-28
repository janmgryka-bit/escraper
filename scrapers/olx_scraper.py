import asyncio
from datetime import datetime
import discord

class OLXScraper:
    def __init__(self, max_budget, database):
        self.max_budget = max_budget
        self.db = database
        self.olx_url = (
            "https://www.olx.pl/elektronika/telefony/smartfony-telefony-komorkowe/warszawa/"
            "q-iphone/?search%5Bdist%5D=50&search%5Bprivate_business%5D=private"
            "&search%5Border%5D=created_at:desc&search%5Bfilter_enum_state%5D%5B0%5D=damaged"
            "&search%5Bfilter_enum_state%5D%5B1%5D=used"
        )
    
    async def scrape(self, context, channel):
        page = await context.new_page()
        await page.route("**/*.{png,jpg,jpeg,webp,gif,svg}", lambda route: route.abort())
        
        try:
            print(f"📡 [{datetime.now().strftime('%H:%M')}] Skanowanie OLX (Top 25)...")
            
            await page.goto(self.olx_url, wait_until="commit", timeout=30000)
            await page.wait_for_selector('div[data-cy="l-card"]', timeout=15000)
            offers = await page.locator('div[data-cy="l-card"]').all()
            
            for offer in offers[:25]:
                try:
                    price_el = offer.locator('p[data-testid="ad-price"]')
                    if await price_el.count() == 0:
                        continue
                    
                    price_text = await price_el.inner_text()
                    price_val = int(''.join(filter(str.isdigit, price_text.split(',')[0])))
                    
                    if price_val > self.max_budget:
                        continue
                    
                    link_el = offer.locator('a').first
                    raw_href = await link_el.get_attribute('href')
                    url = ("https://www.olx.pl" + raw_href if "olx.pl" not in raw_href else raw_href).split('#')[0]
                    
                    if self.db.offer_exists(url):
                        continue
                    
                    full_text = await offer.inner_text()
                    title = full_text.split('\n')[0].lower()
                    
                    if any(x in title for x in ['iphone 7', 'iphone 8', 'iphone x', 'se 2016']):
                        print(f"   🚫 Pomijam stary model: {title[:20]}")
                        continue
                    
                    print(f"🎯 OKAZJA! Próba wysyłki: {title[:30]} | {price_val}zł")
                    
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
                    
                    self.db.add_offer(url, title, price_val)
                    
                except Exception as e:
                    continue
                    
        except Exception as e: 
            print(f"❌ OLX Global Error: {e}")
        finally: 
            if not page.is_closed():
                await page.close()
