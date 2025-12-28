import asyncio
import hashlib
from datetime import datetime
import discord
import logging
import re

logger = logging.getLogger('escraper.fb')

class FacebookScraper:
    def __init__(self, database, config_loader, profit_calculator, ai_analyzer=None):
        self.db = database
        self.config = config_loader
        self.profit_calc = profit_calculator
        self.ai = ai_analyzer
        self.fb_notifications_url = "https://www.facebook.com/notifications"
        self.fb_marketplace_url = "https://www.facebook.com/marketplace/warsaw/search?query=iphone&exact=false"
    
    def _extract_group_name(self, text):
        """
        Wyciąga nazwę grupy z tekstu powiadomienia.
        Przykład: "Teraz w grupie iPhone Kupię / Sprzedam: ..."
        """
        patterns = [
            r'w grupie ([^:]+):',
            r'w grupie ([^"]+)"',
            r'group ([^:]+):',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "Nieznana grupa"
    
    def _extract_post_preview(self, text):
        """
        Wyciąga preview treści posta z powiadomienia.
        """
        if '„' in text and '"' in text:
            start = text.find('„') + 1
            end = text.find('"', start)
            if end > start:
                return text[start:end]
        
        if ':' in text:
            parts = text.split(':', 1)
            if len(parts) > 1:
                return parts[1].strip()[:100]
        
        return text[:100]
    
    def _create_notification_id(self, group_name, preview):
        """
        Tworzy unikalny ID dla powiadomienia (hash z grupy + preview).
        """
        unique_string = f"{group_name}_{preview[:50]}"
        return hashlib.md5(unique_string.encode()).hexdigest()
    
    async def check_notifications(self, context, channel):
        """
        Sprawdza powiadomienia FB, wyciąga nazwę grupy i treść, 
        klika w post i skanuje pełną zawartość.
        """
        page = await context.new_page()
        
        try:
            logger.info("🔔 Rozpoczynam sprawdzanie powiadomień FB...")
            await page.goto(self.fb_notifications_url, timeout=60000)
            logger.info("✅ Strona FB notifications załadowana")
            await asyncio.sleep(3)
            
            # Sprawdź czy zalogowany
            login_check = await page.locator('input[name="email"]').count()
            if login_check > 0:
                logger.warning("⚠️ FB: Sesja wygasła! Wymagane ponowne logowanie")
                await channel.send("⚠️ **Facebook**: Sesja wygasła! Uruchom `python fb_login.py`")
                return
            
            # Próbuj różne selektory dla powiadomień
            notification_selectors = [
                'div[role="article"]',
                'div[role="listitem"]',
                'a[role="link"][href*="/groups/"]',
                'div.x1n2onr6'
            ]
            
            notifications_found = False
            stats = {
                'checked': 0,
                'sent': 0,
                'skipped_duplicate': 0,
                'skipped_irrelevant': 0,
                'skipped_model': 0,
                'skipped_not_profitable': 0
            }
            
            for selector in notification_selectors:
                notif_locator = page.locator(selector)
                count = await notif_locator.count()
                
                if count > 0:
                    logger.info(f"✅ Znaleziono {count} powiadomień (selector: {selector})")
                    notifications_found = True
                    
                    # Sprawdź max 10 najnowszych powiadomień
                    for i in range(min(count, 10)):
                        try:
                            stats['checked'] += 1
                            notif = notif_locator.nth(i)
                            text = await notif.inner_text(timeout=5000)
                            
                            # Sprawdź czy to powiadomienie z grupy
                            if "w grupie" not in text.lower() and "group" not in text.lower():
                                stats['skipped_irrelevant'] += 1
                                continue
                            
                            # Wyciągnij nazwę grupy i preview
                            group_name = self._extract_group_name(text)
                            preview = self._extract_post_preview(text)
                            
                            # Stwórz unikalny ID
                            notification_id = self._create_notification_id(group_name, preview)
                            
                            # Sprawdź czy już było w bazie
                            if self.db.fb_notification_exists(notification_id):
                                stats['skipped_duplicate'] += 1
                                logger.debug(f"🔄 Duplikat FB: {group_name} - {preview[:30]}...")
                                continue
                            
                            # Sprawdź czy zawiera "iphone"
                            if "iphone" not in text.lower():
                                stats['skipped_irrelevant'] += 1
                                continue
                            
                            # Sprawdź czy model jest włączony
                            if not self.config.is_model_enabled(text):
                                stats['skipped_model'] += 1
                                logger.debug(f"🚫 Model wyłączony: {text[:30]}")
                                continue
                            
                            # Kliknij w powiadomienie żeby otworzyć post
                            post_url = None
                            full_content = preview
                            price_val = 0
                            
                            try:
                                # Spróbuj kliknąć i przejść do posta
                                await notif.click(timeout=5000)
                                await asyncio.sleep(3)
                                
                                # Pobierz URL posta (czysty, bez parametrów)
                                current_url = page.url
                                if "groups" in current_url or "posts" in current_url:
                                    # Wyciągnij czysty URL (bez ?notif_id i innych parametrów)
                                    post_url = current_url.split('?')[0]
                                    logger.info(f"   📍 Post URL: {post_url}")
                                    
                                    # Poczekaj na załadowanie treści posta
                                    await asyncio.sleep(3)
                                    
                                    # Spróbuj wyciągnąć PEŁNĄ treść posta (wszystkie div[dir="auto"])
                                    post_selectors = [
                                        'div[data-ad-preview="message"]',
                                        'div[data-ad-comet-preview="message"]',
                                        'div[role="article"]',
                                        'div.x11i5rnm'
                                    ]
                                    
                                    content_parts = []
                                    for post_selector in post_selectors:
                                        content_locators = page.locator(post_selector)
                                        count = await content_locators.count()
                                        if count > 0:
                                            # Zbierz tekst ze wszystkich pasujących elementów
                                            for i in range(min(count, 5)):
                                                try:
                                                    text = await content_locators.nth(i).inner_text(timeout=2000)
                                                    if text and len(text) > 20:
                                                        content_parts.append(text)
                                                except:
                                                    continue
                                            if content_parts:
                                                break
                                    
                                    if content_parts:
                                        full_content = "\n\n".join(content_parts)
                                        logger.info(f"   ✅ Zeskanowano treść posta ({len(full_content)} znaków)")
                                    else:
                                        logger.warning(f"   ⚠️ Nie znaleziono treści posta, używam preview")
                                    
                                    # Wróć do powiadomień
                                    await page.goto(self.fb_notifications_url)
                                    await asyncio.sleep(2)
                                else:
                                    logger.warning(f"   ⚠️ Nie udało się przejść do posta, URL: {current_url}")
                                    
                            except Exception as e:
                                logger.debug(f"   ⚠️ Nie udało się otworzyć posta: {e}")
                            
                            # Spróbuj wyciągnąć cenę z treści (różne formaty)
                            import re
                            price_patterns = [
                                r'(\d+)\s*z[łl]',  # 1500 zł
                                r'cena[:\s]+(\d+)',  # cena: 1500
                                r'(\d+)\s*pln',  # 1500 PLN
                                r'(\d{3,5})(?!\d)',  # same cyfry 3-5 (np. 1500)
                            ]
                            
                            for pattern in price_patterns:
                                price_match = re.search(pattern, full_content, re.IGNORECASE)
                                if price_match:
                                    price_val = int(price_match.group(1))
                                    logger.debug(f"   💰 Znaleziono cenę: {price_val} zł")
                                    break
                            
                            # POMIŃ JEŚLI BRAK CENY
                            if price_val == 0:
                                stats['skipped_irrelevant'] += 1
                                logger.info(f"⏭️  FB: Brak ceny w poście - pomijam: {group_name}")
                                continue
                            
                            # Sprawdź budżet
                            max_budget = self.config.get_max_budget()
                            if price_val > max_budget:
                                stats['skipped_irrelevant'] += 1
                                logger.debug(f"💰 FB: Poza budżetem: {price_val}zł > {max_budget}zł")
                                continue
                            
                            # KALKULACJA OPŁACALNOŚCI
                            profit_result = None
                            if price_val > 0:
                                profit_result = self.profit_calc.calculate(full_content, price_val, full_content)
                                
                                # Sprawdź czy wysyłać
                                discord_config = self.config.get_discord_config()
                                should_send = discord_config['send_all'] or (profit_result and profit_result.get('is_profitable'))
                                
                                if not should_send and profit_result:
                                    stats['skipped_not_profitable'] += 1
                                    logger.info(f"💸 FB Nieopłacalne: {group_name} | {profit_result.get('recommendation', '')}")
                                    continue
                            
                            logger.info(f"🎯 FB: Nowe powiadomienie! Grupa: {group_name}")
                            if profit_result:
                                logger.info(f"   {profit_result.get('recommendation', '')}")
                            
                            # Wyślij na Discord
                            discord_config = self.config.get_discord_config()
                            # Wybierz kolor
                            if profit_result and profit_result.get('is_profitable'):
                                color = discord_config['colors']['profitable']
                            else:
                                color = discord_config['colors']['maybe']
                            
                            # Użyj post_url jeśli jest, inaczej notifications URL
                            final_url = post_url if post_url else self.fb_notifications_url
                            
                            embed = discord.Embed(
                                title=f"🔵 Facebook - {group_name}", 
                                url=final_url, 
                                color=color
                            )
                            
                            # Pokaż PEŁNĄ treść (max 1500 znaków dla Discord)
                            content_display = full_content[:1500]
                            if len(full_content) > 1500:
                                content_display += "..."
                            
                            embed.description = content_display
                            embed.add_field(name="📍 Grupa", value=group_name, inline=False)
                            
                            # Dodaj kalkulację jeśli jest
                            if profit_result and discord_config['send_profit_calc']:
                                profit_text = (
                                    f"**Cena:** {price_val} zł\n"
                                    f"**Model:** {profit_result.get('model', 'Nieznany')}\n"
                                    f"**Stan:** {profit_result.get('condition', 'Nieznany')}\n"
                                    f"**Zysk:** {profit_result.get('potential_profit', 0)} zł\n"
                                    f"**Ocena:** {profit_result.get('recommendation', '')}"
                                )
                                embed.add_field(name="📈 Kalkulacja", value=profit_text, inline=False)
                            
                            embed.set_footer(text="Facebook • Janek Hunter v6.0")
                            
                            try:
                                await channel.send(embed=embed)
                                stats['sent'] += 1
                                logger.info(f"✅ Wysłano powiadomienie FB: {group_name}")
                            except Exception as de:
                                logger.error(f"❌ Błąd Discord: {de}")
                            
                            # Zapisz do bazy
                            self.db.add_fb_notification(notification_id, group_name, full_content, post_url)
                            
                        except Exception as e:
                            logger.debug(f"⚠️ Błąd przetwarzania powiadomienia: {e}")
                            continue
                    
                    break  # Znaleziono powiadomienia, nie sprawdzaj innych selektorów
            
            if not notifications_found:
                logger.warning("⚠️ FB: Nie znaleziono powiadomień (możliwe zmiany w strukturze FB)")
            else:
                logger.info(
                    f"📈 PODSUMOWANIE FB: Sprawdzono={stats['checked']}, "
                    f"Wysłano={stats['sent']}, Pominięto: "
                    f"duplikaty={stats['skipped_duplicate']}, "
                    f"model={stats['skipped_model']}, "
                    f"nieopłacalne={stats['skipped_not_profitable']}, "
                    f"nieistotne={stats['skipped_irrelevant']}"
                )
                
        except Exception as e: 
            logger.error(f"❌ FB Error: {e}")
        finally: 
            await page.close()
    
    async def check_marketplace(self, context, channel):
        """
        Alternative: Check Facebook Marketplace directly for iPhone listings.
        More reliable than notifications.
        """
        page = await context.new_page()
        try:
            logger.info("🛒 Sprawdzam FB Marketplace...")
            await page.goto(self.fb_marketplace_url, timeout=60000)
            await asyncio.sleep(5)
            
            # Check if logged in
            login_check = await page.locator('input[name="email"]').count()
            if login_check > 0:
                logger.warning("⚠️ FB Marketplace: Wymagane logowanie")
                return
            
            logger.info("✅ FB Marketplace załadowany (funkcja w rozwoju)")
            
        except Exception as e:
            logger.error(f"❌ FB Marketplace Error: {e}")
        finally:
            await page.close()
