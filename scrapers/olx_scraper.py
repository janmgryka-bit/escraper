import asyncio
from datetime import datetime
import discord
import logging

logger = logging.getLogger('escraper.olx')

class OLXScraper:
    def __init__(self, database, config_loader, profit_calculator, ai_analyzer=None):
        self.db = database
        self.config = config_loader
        self.profit_calc = profit_calculator
        self.ai = ai_analyzer
        
        # Buduj URL OLX na podstawie konfiguracji
        self.olx_url = self._build_olx_url()
    
    def _build_olx_url(self):
        """Buduje URL OLX na podstawie konfiguracji stanów"""
        base_url = "https://www.olx.pl/elektronika/telefony/smartfony-telefony-komorkowe/warszawa/q-iphone/"
        params = [
            "search%5Bdist%5D=50",
            "search%5Bprivate_business%5D=private",
            "search%5Border%5D=created_at:desc"
        ]
        
        # Dodaj filtry stanów
        conditions = self.config.get_enabled_conditions()
        state_filters = []
        
        if 'uszkodzony' in conditions or 'na_czesci' in conditions:
            state_filters.append("search%5Bfilter_enum_state%5D%5B0%5D=damaged")
        if 'uzywany' in conditions:
            state_filters.append("search%5Bfilter_enum_state%5D%5B1%5D=used")
        if 'nowy' in conditions:
            state_filters.append("search%5Bfilter_enum_state%5D%5B2%5D=new")
        
        params.extend(state_filters)
        return base_url + "?" + "&".join(params)
    
    async def scrape(self, context, channel):
        page = await context.new_page()
        await page.route("**/*.{png,jpg,jpeg,webp,gif,svg}", lambda route: route.abort())
        
        try:
            logger.info("🔍 Rozpoczynam skanowanie OLX...")
            logger.info(f"🔗 URL: {self.olx_url}")
            
            await page.goto(self.olx_url, wait_until="commit", timeout=30000)
            logger.info("✅ Strona OLX załadowana")
            
            await page.wait_for_selector('div[data-cy="l-card"]', timeout=15000)
            offers = await page.locator('div[data-cy="l-card"]').all()
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
            
            # Lista ofert do smart matching
            all_offers = []
            
            for offer in offers[:25]:
                try:
                    stats['checked'] += 1
                    
                    # Pobierz cenę
                    price_el = offer.locator('p[data-testid="ad-price"]')
                    if await price_el.count() == 0:
                        stats['skipped_no_price'] += 1
                        continue
                    
                    price_text = await price_el.inner_text()
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
                    url = ("https://www.olx.pl" + raw_href if "olx.pl" not in raw_href else raw_href).split('#')[0]
                    
                    # Pobierz tytuł i opis
                    full_text = await offer.inner_text()
                    title = full_text.split('\n')[0]
                    
                    # Sprawdź duplikaty na podstawie treści (300 znaków)
                    if self.db.offer_exists(full_text):
                        stats['skipped_duplicate'] += 1
                        logger.debug(f"🔄 Duplikat: {title[:30]}...")
                        continue
                    
                    # Sprawdź czy model jest włączony
                    if not self.config.is_model_enabled(title):
                        stats['skipped_model'] += 1
                        logger.debug(f"🚫 Model wyłączony: {title[:30]}")
                        continue
                    
                    # KALKULACJA OPŁACALNOŚCI
                    profit_result = self.profit_calc.calculate(title, price_val, full_text)
                    
                    if not profit_result.get('model'):
                        stats['skipped_model'] += 1
                        logger.debug(f"❓ Nieznany model: {title[:30]}")
                        continue
                    
                    # Dodaj do listy dla smart matching
                    profit_result['url'] = url
                    profit_result['title'] = title
                    profit_result['full_text'] = full_text
                    all_offers.append(profit_result)
                    
                    # Wyciągnij URL-e zdjęć (jeśli AI ma analizować obrazy)
                    image_urls = []
                    if self.ai and self.ai.enabled and self.ai.ai_config['checks'].get('analyze_images', False):
                        try:
                            img_elements = await offer.locator('img').all()
                            for img in img_elements[:3]:  # Max 3 zdjęcia
                                img_src = await img.get_attribute('src')
                                if img_src and 'http' in img_src:
                                    image_urls.append(img_src)
                            if image_urls:
                                logger.debug(f"📸 Znaleziono {len(image_urls)} zdjęć dla AI")
                        except Exception as e:
                            logger.debug(f"⚠️ Nie udało się pobrać zdjęć: {e}")
                    
                    # AI Analiza (opcjonalne)
                    ai_result = None
                    if self.ai and self.ai.enabled:
                        ai_result = self.ai.analyze_offer(
                            profit_result['model'],
                            price_val,
                            title,
                            full_text,
                            image_urls=image_urls if image_urls else None
                        )
                        
                        # Jeśli AI wykryło oszustwo, pomiń
                        if ai_result and ai_result.get('is_scam'):
                            stats['skipped_ai'] += 1
                            logger.warning(f"⚠️ AI wykryło oszustwo: {title[:30]}")
                            continue
                    
                    # Sprawdź czy wysyłać (tylko opłacalne lub wszystkie)
                    discord_config = self.config.get_discord_config()
                    should_send = discord_config['send_all'] or profit_result['is_profitable']
                    
                    if not should_send:
                        stats['skipped_not_profitable'] += 1
                        logger.info(f"💸 Nieopłacalne: {title[:30]} | {profit_result['recommendation']}")
                        continue
                    
                    # WYŚLIJ NA DISCORD
                    logger.info(f"🎯 ZNALEZIONO: {title[:40]} | {price_val}zł")
                    logger.info(f"   {profit_result['recommendation']}")
                    
                    try:
                        # Wybierz kolor embeda
                        if profit_result['is_profitable']:
                            if profit_result['potential_profit'] >= profit_result['min_profit'] * 2:
                                color = discord_config['colors']['profitable']  # Zielony - super okazja
                            else:
                                color = discord_config['colors']['maybe']  # Żółty - ok
                        else:
                            color = discord_config['colors']['not_profitable']  # Czerwony
                        
                        logger.debug(f"   📝 Tworzę embed...")
                        embed = discord.Embed(
                            title=f"📱 {profit_result['model'].upper()}", 
                            url=url, 
                            color=color,
                            description=title[:200]
                        )
                    except Exception as embed_err:
                        logger.error(f"❌ Błąd tworzenia embeda: {embed_err}")
                        continue
                    
                    # Podstawowe info
                    embed.add_field(name="💰 Cena", value=f"**{price_val} zł**", inline=True)
                    embed.add_field(name="📊 Stan", value=profit_result['condition'], inline=True)
                    
                    # Kalkulacja zysku (jeśli włączone)
                    if discord_config['send_profit_calc']:
                        profit_text = (
                            f"**Zakup:** {profit_result['buy_price']} zł\n"
                            f"**Naprawa:** {profit_result['repair_cost']} zł\n"
                            f"**Razem:** {profit_result['total_cost']} zł\n"
                            f"**Sprzedaż:** {profit_result['market_price']} zł\n"
                            f"**ZYSK:** {profit_result['potential_profit']} zł ({profit_result['profit_margin']:.1f}%)"
                        )
                        embed.add_field(name="📈 Kalkulacja", value=profit_text, inline=False)
                    
                    # Rekomendacja
                    embed.add_field(name="✅ Ocena", value=profit_result['recommendation'], inline=False)
                    
                    # AI Analiza (jeśli włączone)
                    if ai_result and discord_config['send_ai_analysis']:
                        reasoning = str(ai_result.get('ai_reasoning', 'Brak szczegółów'))
                        ai_text = (
                            f"**Stan:** {ai_result.get('condition_score', 5)}/10\n"
                            f"**Warto:** {'✅ TAK' if ai_result.get('worth_buying', False) else '❌ NIE'}\n"
                            f"**Uwagi:** {reasoning[:100]}..."
                        )
                        
                        # Dodaj analizę zdjęć jeśli jest
                        if ai_result.get('image_analysis'):
                            ai_text += f"\n\n**📸 Analiza zdjęć:**\n{ai_result['image_analysis'][:150]}..."
                            if ai_result.get('visible_damages'):
                                ai_text += f"\n**Uszkodzenia:** {', '.join(ai_result['visible_damages'])}"
                            if not ai_result.get('photos_authentic', True):
                                ai_text += "\n⚠️ **Zdjęcia mogą być stock photos!**"
                        
                        embed.add_field(name="🤖 AI Analiza", value=ai_text, inline=False)
                    
                    # Uszkodzenia (jeśli są)
                    if profit_result['damages']:
                        embed.add_field(
                            name="⚠️ Uszkodzenia", 
                            value=", ".join(profit_result['damages']), 
                            inline=False
                        )
                    
                    embed.set_footer(text=f"OLX • Janek Hunter v6.0")
                    
                    try:
                        if channel:
                            await channel.send(embed=embed)
                            stats['sent'] += 1
                            logger.info(f"✅ Wysłano na Discord: {title[:30]}")
                        else:
                            logger.error(f"❌ Channel is None - nie można wysłać!")
                            stats['sent'] += 1  # Liczy jako wysłane żeby nie blokować
                    except Exception as de:
                        logger.error(f"❌ Błąd Discord: {de}")
                        import traceback
                        logger.error(traceback.format_exc())
                    
                    # Zapisz do bazy (używając treści jako unique ID)
                    self.db.add_offer(full_text, url, title, price_val, 'olx')
                    
                except Exception as e:
                    logger.error(f"❌ Błąd przetwarzania oferty: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    continue
            
            # SMART MATCHING
            if self.config.is_smart_matching_enabled() and len(all_offers) >= 2:
                logger.info("💡 Szukam inteligentnych połączeń...")
                matches = self.profit_calc.find_smart_matches(all_offers)
                
                if matches and discord_config['send_smart_matches']:
                    for match in matches[:3]:  # Max 3 najlepsze
                        await self._send_smart_match(channel, match, discord_config)
            
            # Podsumowanie
            logger.info(
                f"📈 PODSUMOWANIE OLX: Sprawdzono={stats['checked']}, "
                f"Wysłano={stats['sent']}, Pominięto: "
                f"budżet={stats['skipped_budget']}, "
                f"duplikaty={stats['skipped_duplicate']}, "
                f"model={stats['skipped_model']}, "
                f"nieopłacalne={stats['skipped_not_profitable']}, "
                f"brak_ceny={stats['skipped_no_price']}"
            )
                    
        except Exception as e: 
            logger.error(f"❌ OLX Global Error: {e}")
        finally: 
            if not page.is_closed():
                await page.close()
    
    async def _send_smart_match(self, channel, match, discord_config):
        """Wysyła propozycję inteligentnego połączenia na Discord"""
        try:
            embed = discord.Embed(
                title=f"💡 INTELIGENTNE POŁĄCZENIE - {match['model'].upper()}",
                color=discord_config['colors']['smart_match'],
                description=f"**Typ:** {match['combination_type']}"
            )
            
            # Oferta 1
            offer1 = match['offer1']
            embed.add_field(
                name="📱 Oferta 1",
                value=f"Cena: {offer1['buy_price']} zł\nStan: {offer1['condition']}\n[Link]({offer1['url']})",
                inline=True
            )
            
            # Oferta 2
            offer2 = match['offer2']
            embed.add_field(
                name="📱 Oferta 2",
                value=f"Cena: {offer2['buy_price']} zł\nStan: {offer2['condition']}\n[Link]({offer2['url']})",
                inline=True
            )
            
            # Kalkulacja
            calc_text = (
                f"**Zakup:** {offer1['buy_price']} + {offer2['buy_price']} = {offer1['buy_price'] + offer2['buy_price']} zł\n"
                f"**Montaż:** ~{match['combined_cost'] - offer1['buy_price'] - offer2['buy_price']} zł\n"
                f"**Razem:** {match['combined_cost']} zł\n"
                f"**Sprzedaż:** {match['market_price']} zł\n"
                f"**ZYSK:** {match['potential_profit']} zł ({match['profit_margin']:.1f}%)"
            )
            embed.add_field(name="📈 Kalkulacja", value=calc_text, inline=False)
            embed.add_field(name="✅ Rekomendacja", value=match['recommendation'], inline=False)
            
            embed.set_footer(text="Smart Matching • Janek Hunter v6.0")
            
            await channel.send(embed=embed)
            logger.info(f"💡 Wysłano smart match: {match['model']} | Zysk: {match['potential_profit']}zł")
            
        except Exception as e:
            logger.error(f"❌ Błąd wysyłania smart match: {e}")
