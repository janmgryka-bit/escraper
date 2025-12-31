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
        self.fb_notifications_url = "https://m.facebook.com/notifications"
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
    
    async def bypass_fb_cookies(self, page):
        """
        Omija okno Cookie Consent na Facebooku.
        Szuka i klika przyciski akceptacji cookies.
        """
        logger.info("🍪 [FB] Sprawdzam okno Cookie Consent...")
        print("DEBUG: Sprawdzam czy wystąpiło okno cookies...")
        
        cookie_selectors = [
            ('button:has-text("Zezwól na wszystkie pliki cookie")', 'Polski: Zezwól na wszystkie'),
            ('button:has-text("Akceptuj wszystkie")', 'Polski: Akceptuj wszystkie'),
            ('button:has-text("Allow all cookies")', 'Angielski: Allow all cookies'),
            ('button:has-text("Accept All")', 'Angielski: Accept All'),
            ('button[data-cookiebanner="accept_button"]', 'Data attribute: accept_button'),
            ('button[title="Accept All"]', 'Title: Accept All'),
            ('div[aria-label="Zezwól na wszystkie pliki cookie"]', 'Aria-label: Zezwól'),
            ('div[aria-label="Allow all cookies"]', 'Aria-label: Allow')
        ]
        
        cookie_found = False
        for selector, description in cookie_selectors:
            try:
                cookie_button = page.locator(selector).first
                # Czekaj max 3 sekundy na przycisk
                await cookie_button.wait_for(state="visible", timeout=3000)
                
                if await cookie_button.is_visible():
                    logger.info(f"🍪 [FB] Wykryto okno cookies: {description}")
                    print(f"DEBUG: Wykryto okno cookies, próbuję kliknąć przycisk: {description}")
                    
                    # Kliknij przycisk
                    await cookie_button.click()
                    logger.info("✅ [FB] Kliknięto przycisk akceptacji cookies")
                    
                    # Czekaj na zniknięcie okna
                    await asyncio.sleep(2)
                    
                    # Zrób screenshot po kliknięciu
                    try:
                        await page.screenshot(path='fb_after_cookie.png')
                        logger.info("📸 [FB] Screenshot po kliknięciu cookies: fb_after_cookie.png")
                        print("DEBUG: Screenshot zapisany jako fb_after_cookie.png")
                    except Exception as e:
                        logger.warning(f"⚠️ [FB] Nie udało się zrobić screenshota: {e}")
                    
                    cookie_found = True
                    break
            except Exception:
                # Ten selektor nie zadziałał, próbuj następny
                continue
        
        if not cookie_found:
            logger.info("✅ [FB] Okno cookies nie wystąpiło lub już zaakceptowane")
            print("DEBUG: Okno cookies nie wystąpiło")
        
        return cookie_found
    
    async def check_notifications(self, context, channel):
        """
        Sprawdza powiadomienia FB, wyciąga nazwę grupy i treść, 
        klika w post i skanuje pełną zawartość.
        """
        logger.info("🔔 [FB] Rozpoczynam sprawdzanie powiadomień FB...")
        
        try:
            page = await context.new_page()
            logger.info("🔔 [FB] Próba otwarcia sesji FB...")
        except Exception as e:
            logger.error(f"❌ [FB] Błąd tworzenia strony: {e}")
            if channel:
                await channel.send("⚠️ **Sesja FB wygasła!** Zaloguj się ponownie.")
            return
        
        try:
            logger.info("🔔 [FB] Ładowanie strony powiadomień (mobile)...")
            await page.goto(self.fb_notifications_url, timeout=60000)
            logger.info("✅ [FB] Strona FB notifications załadowana")
            
            # Czekaj na pełne załadowanie sieci (daje czas na aktywację sesji)
            logger.info("⏳ [FB] Czekam na networkidle...")
            await page.wait_for_load_state("networkidle", timeout=15000)
            await asyncio.sleep(2)
            
            # KROK 1: Omiń okno Cookie Consent (dedykowana funkcja)
            await self.bypass_fb_cookies(page)
            
            # KROK 2: Inteligentne sprawdzenie sesji
            logger.info("🔔 [FB] Sprawdzam sesję logowania...")
            
            # Sprawdź czy to faktycznie formularz logowania czy tylko cookies
            login_check = await page.locator('input[name="email"]').count()
            password_check = await page.locator('input[name="pass"]').count()
            
            if login_check > 0 and password_check > 0:
                logger.warning("⚠️ [FB] Wykryto formularz logowania - próbuję automatycznego logowania...")
                
                # Spróbuj zalogować się automatycznie z .env
                import os
                fb_email = os.getenv('FB_EMAIL')
                fb_password = os.getenv('FB_PASSWORD')
                
                if fb_email and fb_password:
                    try:
                        logger.info("🔐 [FB] Próba automatycznego logowania...")
                        await page.fill('input[name="email"]', fb_email)
                        await asyncio.sleep(1)
                        await page.fill('input[name="pass"]', fb_password)
                        await asyncio.sleep(1)
                        await page.click('button[name="login"], input[name="login"]')
                        logger.info("⏳ [FB] Czekam na zalogowanie...")
                        await asyncio.sleep(5)
                        
                        # Sprawdź czy logowanie się powiodło
                        if await page.locator('input[name="email"]').count() > 0:
                            logger.error("❌ [FB] Automatyczne logowanie nie powiodło się")
                            await page.screenshot(path='fb_error.png')
                            logger.info("📸 [FB] Screenshot błędu zapisany jako fb_error.png")
                            if channel:
                                await channel.send("⚠️ **Sesja FB wygasła!** Automatyczne logowanie nie powiodło się. Uruchom: `docker exec -it janek_hunter python fb_login.py`")
                            await page.close()
                            return
                        else:
                            logger.info("✅ [FB] Automatyczne logowanie powiodło się!")
                    except Exception as e:
                        logger.error(f"❌ [FB] Błąd automatycznego logowania: {e}")
                        await page.screenshot(path='fb_error.png')
                        if channel:
                            await channel.send("⚠️ **Sesja FB wygasła!** Uruchom: `docker exec -it janek_hunter python fb_login.py`")
                        await page.close()
                        return
                else:
                    logger.error("❌ [FB] Brak FB_EMAIL/FB_PASSWORD w .env - nie mogę zalogować automatycznie")
                    await page.screenshot(path='fb_error.png')
                    logger.info("📸 [FB] Screenshot błędu zapisany jako fb_error.png")
                    if channel:
                        await channel.send("⚠️ **Sesja FB wygasła!** Dodaj FB_EMAIL i FB_PASSWORD do .env, potem uruchom: `docker exec -it janek_hunter python fb_login.py`")
                    await page.close()
                    return
            
            logger.info("✅ [FB] Sesja aktywna, szukam powiadomień...")
            
            # KROK 1: Idź bezpośrednio do powiadomień
            logger.info("🔔 [FB] Idę bezpośrednio do powiadomień...")
            
            try:
                # Idź bezpośrednio do strony powiadomień
                await page.goto("https://m.facebook.com/notifications", timeout=30000)
                await page.wait_for_load_state("networkidle", timeout=10000)
                logger.info("✅ [FB] Załadowano stronę powiadomień")
                
                # DEBUG: Zrób screenshot listy powiadomień
                await page.screenshot(path='fb_notifications.png')
                logger.info("📸 [FB] Screenshot listy powiadomień zapisany jako fb_notifications.png")
                
            except Exception as e:
                logger.error(f"❌ [FB] Nie udało się załadować powiadomień: {e}")
                await page.screenshot(path='fb_error.png')
                logger.info("📸 [FB] Screenshot błędu zapisany jako fb_error.png")
                if channel:
                    await channel.send("⚠️ **FB:** Nie udało się załadować powiadomień. Sprawdź fb_error.png")
                return
            
            # KROK 2: Przeszukaj listę powiadomień - użyj robust selector dla mobile
            notification_selectors = [
                'xpath=//div[@id="notifications_list"]//a',  # Robust selector dla mobile
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
                logger.debug(f"🔍 [FB] Próbuję selektora: {selector}")
                notif_locator = page.locator(selector)
                count = await notif_locator.count()
                
                if count > 0:
                    logger.info(f"✅ [FB] Znaleziono {count} powiadomień (selector: {selector})")
                    notifications_found = True
                    
                    # Sprawdź max 10 najnowszych powiadomień
                    for i in range(min(count, 10)):
                        try:
                            stats['checked'] += 1
                            notif = notif_locator.nth(i)
                            text = await notif.inner_text(timeout=5000)
                            
                            # KROK 3: Sprawdź czy to powiadomienie o sprzedaży
                            sales_keywords = ['dodał post', 'added a post', 'sprzedam', 'nowa oferta', 'for sale', 'na sprzedaż']
                            is_sales_notification = any(keyword in text.lower() for keyword in sales_keywords)
                            
                            if not is_sales_notification:
                                stats['skipped_irrelevant'] += 1
                                logger.debug(f"🚫 [FB] Nie jest powiadomieniem o sprzedaży: {text[:50]}...")
                                continue
                            
                            # Sprawdź czy zawiera "iphone"
                            if "iphone" not in text.lower():
                                stats['skipped_irrelevant'] += 1
                                continue
                            
                            # Wyciągnij nazwę grupy i preview
                            group_name = self._extract_group_name(text)
                            preview = self._extract_post_preview(text)
                            
                            logger.info(f"🎯 [FB] Znaleziono powiadomienie o sprzedaży: {group_name} - {preview[:50]}...")
                            
                            # Sprawdź czy model jest włączony
                            if not self.config.is_model_enabled(text):
                                stats['skipped_model'] += 1
                                logger.debug(f"🚫 Model wyłączony: {text[:30]}")
                                continue
                            
                            # KROK 4: Kliknij powiadomienie aby otworzyć post
                            try:
                                # Przewiń element do widoku i kliknij
                                await notif.scroll_into_view_if_needed(timeout=3000)
                                await asyncio.sleep(0.5)
                                await notif.click(timeout=10000, force=True)
                                await asyncio.sleep(3)
                                
                                logger.info(f"🔗 [FB] Kliknięto powiadomienie, otwieram post...")
                                
                                # Pobierz rzeczywisty URL po kliknięciu
                                current_url = page.url
                                logger.info(f"   📍 Obecny URL: {current_url}")
                                
                                # Spróbuj wyciągnąć pełną treść posta
                                full_content = preview
                                post_url = current_url
                                
                                try:
                                    # Sprawdź czy jesteśmy w poście
                                    if "posts" in current_url or "permalink" in current_url:
                                        logger.info(f"📄 [FB] Jesteśmy w poście, pobieram treść...")
                                        
                                        # Poczekaj na załadowanie treści
                                        await page.wait_for_load_state("networkidle", timeout=5000)
                                        
                                        # Spróbuj wyciągnąć pełną treść posta
                                        content_selectors = [
                                            'div[data-ad-preview="message"]',
                                            'div[data-testid="post_message"]',
                                            'div.x1i10hfl',
                                            'div.x1n2onr6'
                                        ]
                                        
                                        for content_sel in content_selectors:
                                            content_el = page.locator(content_sel)
                                            if await content_el.count() > 0:
                                                try:
                                                    post_text = await content_el.first.inner_text(timeout=3000)
                                                    if post_text and len(post_text.strip()) > 50:
                                                        full_content = post_text
                                                        logger.info(f"✅ [FB] Pobrano pełną treść posta ({len(full_content)} znaków)")
                                                        break
                                                except:
                                                    continue
                                except Exception as e:
                                    logger.warning(f"⚠️ [FB] Nie udało się pobrać pełnej treści: {e}")
                                
                                # KROK 5: Wyodrębnij cenę z treści
                                import re
                                price_patterns = [
                                    r'(\d+)\s*z[łl]',  # 1500 zł
                                    r'cena[:\s]+(\d+)',  # cena: 1500
                                    r'(\d+)\s*pln',  # 1500 PLN
                                    r'(\d{3,5})(?!\d)',  # same cyfry 3-5 (np. 1500)
                                ]
                                
                                price_val = 0
                                for pattern in price_patterns:
                                    match = re.search(pattern, full_content.lower())
                                    if match:
                                        price_val = int(match.group(1))
                                        logger.info(f"� [FB] Wyodrębniono cenę: {price_val}zł")
                                        break
                                
                                if price_val == 0:
                                    logger.info(f"⏭️  FB: Brak ceny w poście - pomijam: {group_name}")
                                    continue
                            
                            # KROK 6: ABSOLUTE DUPLICATE LOCK - użyj get_offer_hash i commit_or_abort
                                content_hash = self.db.get_offer_hash(group_name, price_val, full_content, "Facebook")
                                
                                # COMMIT OR ABORT LOGIC - IMMEDIATE DB INSERT
                                if not self.db.commit_or_abort(content_hash, group_name, price_val, post_url):
                                    stats['skipped_duplicate'] += 1
                                    logger.info(f"� [FB] ABORT - Duplicate detected: {group_name}")
                                    # Wróć do listy powiadomień
                                    await page.goto(self.fb_notifications_url)
                                    await asyncio.sleep(2)
                                    continue  # NATYCHMIASTOWE ABORT
                                
                                # Sprawdź budżet
                                max_budget = self.config.get_max_budget()
                                if price_val > max_budget:
                                    stats['skipped_irrelevant'] += 1
                                    logger.debug(f"💰 FB: Poza budżetem: {price_val}zł > {max_budget}zł")
                                    # Wróć do listy powiadomień
                                    await page.goto(self.fb_notifications_url)
                                    await asyncio.sleep(2)
                                    continue
                                    
                            except Exception as e:
                                logger.warning(f"   ⚠️ Nie udało się otworzyć posta: {e}")
                                full_content = preview
                            
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
                            
                            # ZAWSZE użyj post_url - jeśli nie ma, pomiń post
                            if not post_url:
                                logger.warning(f"⚠️ Brak post_url dla: {group_name} - pomijam")
                                continue
                            
                            embed = discord.Embed(
                                title=f"🔵 Facebook - {group_name}", 
                                url=post_url, 
                                color=color
                            )
                            
                            # PEŁNY OPIS (do 4000 znaków zgodnie z limitem Discord)
                            embed.description = full_content[:4000]
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
                            
                            # Zapisz do bazy PRZED wysłaniem na Discord (pancerne rozwiązanie z content_hash)
                            if not self.db.add_offer(group_name, price_val, full_content, post_url, location="Facebook", source='facebook'):
                                logger.warning(f"⚠️ [FB] Powiadomienie już istnieje w bazie (content_hash): {group_name}")
                                stats['skipped_duplicate'] += 1
                                continue
                            
                        except Exception as e:
                            logger.debug(f"⚠️ Błąd przetwarzania powiadomienia: {e}")
                            continue
                    
                    break  # Znaleziono powiadomienia, nie sprawdzaj innych selektorów
            
            if not notifications_found:
                logger.warning("⚠️ [FB] Nie znaleziono żadnych powiadomień FB (sprawdzono wszystkie selektory)")
                logger.warning("⚠️ [FB] Możliwe przyczyny: brak nowych powiadomień, zmiana struktury FB, lub nieaktualne selektory CSS")
                if channel:
                    await channel.send("⚠️ **FB:** Brak nowych powiadomień lub selektory CSS wymagają aktualizacji.")
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
