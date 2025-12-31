import asyncio
from datetime import datetime
import discord
import logging

logger = logging.getLogger('escraper.allegro')

class AllegroScraper:
    def __init__(self, database, config_loader, profit_calculator, ai_analyzer=None):
        self.db = database
        self.config = config_loader
        self.profit_calc = profit_calculator
        self.ai = ai_analyzer
        
        # URL Allegro Lokalnie - użytkownik ustawi filtry ręcznie
        self.allegro_url = self._build_allegro_url()
    
    def _build_allegro_url(self):
        """Buduje URL Allegro Lokalnie na podstawie konfiguracji"""
        # Bazowy URL z filtrami (użytkownik może dostosować w config.yaml)
        allegro_config = self.config.config.get('sources', {}).get('allegro_lokalnie', {})
        return allegro_config.get('url', 'https://allegrolokalnie.pl/oferty/q/iphone')
    
    async def scrape(self, context, channel):
        page = await context.new_page()
        await page.route("**/*.{png,jpg,jpeg,webp,gif,svg}", lambda route: route.abort())
        
        try:
            logger.info("🔍 Rozpoczynam skanowanie Allegro Lokalnie...")
            logger.info(f"🔗 URL: {self.allegro_url}")
            
            await page.goto(self.allegro_url, wait_until="domcontentloaded", timeout=30000)
            logger.info("✅ Strona Allegro Lokalnie załadowana")
            
            # Poczekaj na załadowanie ofert
            await asyncio.sleep(3)
            
            # Allegro Lokalnie używa article jako kontener oferty
            await page.wait_for_selector('article', timeout=15000)
            offers = await page.locator('article').all()
            logger.info(f"📊 Znaleziono {len(offers)} ogłoszeń na stronie")
            
            # Statystyki
            stats = {
                'checked': 0,
                'sent': 0,
                'skipped_no_price': 0,
                'skipped_budget': 0,
                'skipped_duplicate': 0,
                'skipped_model': 0,
                'skipped_not_profitable': 0,
                'skipped_ai': 0
            }
            
            max_budget = self.config.get_max_budget()
            
            for offer in offers[:25]:
                try:
                    stats['checked'] += 1
                    
                    # Pobierz tytuł
                    title_el = offer.locator('h2, h3, [data-testid="listing-title"]')
                    if await title_el.count() == 0:
                        continue
                    title = await title_el.first.inner_text()
                    
                    # Sprawdź czy zawiera "iphone"
                    if "iphone" not in title.lower():
                        stats['skipped_model'] += 1
                        continue
                    
                    # Sprawdź czy model jest włączony
                    if not self.config.is_model_enabled(title):
                        stats['skipped_model'] += 1
                        logger.debug(f"🚫 Model wyłączony: {title[:30]}")
                        continue
                    
                    # Pobierz cenę - Allegro Lokalnie używa różnych selektorów
                    price_el = offer.locator('[data-testid="listing-price"], .price, [class*="price"]')
                    if await price_el.count() == 0:
                        stats['skipped_no_price'] += 1
                        continue
                    
                    price_text = await price_el.first.inner_text()
                    price_digits = ''.join(filter(str.isdigit, price_text.split(',')[0]))
                    if not price_digits:
                        stats['skipped_no_price'] += 1
                        logger.debug(f"⚠️ Brak ceny w tekście: {price_text}")
                        continue
                    price_val = int(price_digits)
                    
                    # Sprawdź budżet
                    if price_val > max_budget:
                        stats['skipped_budget'] += 1
                        logger.debug(f"💰 Poza budżetem: {price_val}zł > {max_budget}zł")
                        continue
                    
                    # Pobierz URL
                    link_el = offer.locator('a').first
                    raw_href = await link_el.get_attribute('href')
                    full_url = "https://allegrolokalnie.pl" + raw_href if "allegrolokalnie.pl" not in raw_href else raw_href
                    
                    # Usuń tylko hash, zostaw query params (potrzebne do działania linku)
                    url = full_url.split('#')[0]
                    
                    # Pobierz opis (jeśli dostępny na liście)
                    desc_el = offer.locator('[data-testid="listing-description"], .description, p')
                    description = ""
                    if await desc_el.count() > 0:
                        try:
                            description = await desc_el.first.inner_text(timeout=2000)
                        except:
                            description = title
                    else:
                        description = title
                    
                    # ABSOLUTE DUPLICATE LOCK - użyj get_offer_hash i commit_or_abort
                    content_hash = self.db.get_offer_hash(title, price_val, description, "Warszawa")
                    
                    # COMMIT OR ABORT LOGIC - IMMEDIATE DB INSERT
                    if not self.db.commit_or_abort(content_hash, title, price_val, url):
                        stats['skipped_duplicate'] += 1
                        logger.info(f"🔄 [Allegro] ABORT - Duplicate detected: {title[:30]}")
                        continue  # NATYCHMIASTOWE ABORT
                    
                    # KALKULACJA OPŁACALNOŚCI
                    profit_result = self.profit_calc.calculate(title, price_val, description)
                    
                    # AI Analiza (jeśli włączona)
                    ai_result = None
                    if self.ai and self.ai.enabled:
                        try:
                            ai_result = await self.ai.analyze_offer(title, price_val, description, [])
                        except Exception as ai_err:
                            logger.debug(f"⚠️ AI analiza nie powiodła się: {ai_err}")
                            stats['skipped_ai'] += 1
                    
                    # Sprawdź czy wysyłać
                    discord_config = self.config.get_discord_config()
                    should_send = discord_config['send_all'] or (profit_result and profit_result.get('is_profitable'))
                    
                    if not should_send and profit_result:
                        stats['skipped_not_profitable'] += 1
                        logger.info(f"💸 Allegro nieopłacalne: {title[:40]} | {profit_result.get('recommendation', '')}")
                        continue
                    
                    logger.info(f"🎯 ZNALEZIONO: {title} | {price_val}zł")
                    if profit_result:
                        logger.info(f"   {profit_result.get('recommendation', '')}")
                    
                    # Wyślij na Discord
                    if profit_result and profit_result.get('is_profitable'):
                        color = discord_config['colors']['profitable']
                    else:
                        color = discord_config['colors']['maybe']
                    
                    embed = discord.Embed(
                        title=f"🟣 Allegro Lokalnie - {title[:100]}", 
                        url=url, 
                        color=color
                    )
                    
                    # PEŁNY OPIS (do 4000 znaków zgodnie z limitem Discord)
                    embed.description = content[:4000]
                    
                    # Dodaj kalkulację
                    if profit_result and discord_config['send_profit_calc']:
                        profit_text = (
                            f"**Cena:** {price_val} zł\n"
                            f"**Model:** {profit_result.get('model', 'Nieznany')}\n"
                            f"**Stan:** {profit_result.get('condition', 'Nieznany')}\n"
                            f"**Zysk:** {profit_result.get('potential_profit', 0)} zł\n"
                            f"**Ocena:** {profit_result.get('recommendation', '')}"
                        )
                        embed.add_field(name="📈 Kalkulacja", value=profit_text, inline=False)
                    
                    # Dodaj AI analizę
                    if ai_result and discord_config['send_ai_analysis']:
                        try:
                            reasoning = ai_result.get('ai_reasoning', 'Brak szczegółów')
                            if not isinstance(reasoning, str):
                                reasoning = str(reasoning)
                            condition_score = ai_result.get('condition_score', 5)
                            worth_buying = ai_result.get('worth_buying', False)
                            ai_text = (
                                f"**Stan:** {condition_score}/10\n"
                                f"**Warto:** {'✅ TAK' if worth_buying else '❌ NIE'}\n"
                                f"**Uwagi:** {reasoning[:100]}..."
                            )
                            embed.add_field(name="🤖 AI Analiza", value=ai_text, inline=False)
                        except Exception as ai_err:
                            logger.warning(f"⚠️ Błąd formatowania AI: {ai_err}")
                    
                    embed.set_footer(text="Allegro Lokalnie • Janek Hunter v6.0")
                    
                    # JUŻ ZAPISANE W BAZIE PRZEZ commit_or_abort() - kontynuuj do Discord
                    
                    try:
                        await channel.send(embed=embed)
                        stats['sent'] += 1
                        logger.info(f"✅ Wysłano na Discord: {title[:40]}")
                    except Exception as de:
                        logger.error(f"❌ Błąd Discord: {de}")
                    
                except Exception as e:
                    logger.error(f"❌ Błąd przetwarzania oferty: {e}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    continue
            
            logger.info(
                f"📈 PODSUMOWANIE Allegro: Sprawdzono={stats['checked']}, Wysłano={stats['sent']}, "
                f"Pominięto: budżet={stats['skipped_budget']}, duplikaty={stats['skipped_duplicate']}, "
                f"model={stats['skipped_model']}, nieopłacalne={stats['skipped_not_profitable']}, brak_ceny={stats['skipped_no_price']}"
            )
            
        except Exception as e:
            logger.error(f"❌ Błąd skanowania Allegro: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        finally:
            await page.close()
