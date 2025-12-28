import asyncio
import hashlib
from datetime import datetime
import discord
import logging
import re

logger = logging.getLogger('escraper.fb')

class FacebookScraper:
    def __init__(self, database):
        self.db = database
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
            checked = 0
            sent = 0
            skipped_duplicate = 0
            skipped_irrelevant = 0
            
            for selector in notification_selectors:
                notif_locator = page.locator(selector)
                count = await notif_locator.count()
                
                if count > 0:
                    logger.info(f"✅ Znaleziono {count} powiadomień (selector: {selector})")
                    notifications_found = True
                    
                    # Sprawdź max 10 najnowszych powiadomień
                    for i in range(min(count, 10)):
                        try:
                            checked += 1
                            notif = notif_locator.nth(i)
                            text = await notif.inner_text(timeout=5000)
                            
                            # Sprawdź czy to powiadomienie z grupy
                            if "w grupie" not in text.lower() and "group" not in text.lower():
                                skipped_irrelevant += 1
                                continue
                            
                            # Wyciągnij nazwę grupy i preview
                            group_name = self._extract_group_name(text)
                            preview = self._extract_post_preview(text)
                            
                            # Stwórz unikalny ID
                            notification_id = self._create_notification_id(group_name, preview)
                            
                            # Sprawdź czy już było w bazie
                            if self.db.fb_notification_exists(notification_id):
                                skipped_duplicate += 1
                                logger.debug(f"🔄 Duplikat FB: {group_name} - {preview[:30]}...")
                                continue
                            
                            # Sprawdź czy zawiera "iphone"
                            if "iphone" not in text.lower():
                                skipped_irrelevant += 1
                                continue
                            
                            logger.info(f"🎯 FB: Nowe powiadomienie! Grupa: {group_name}")
                            logger.info(f"   Preview: {preview[:50]}...")
                            
                            # Kliknij w powiadomienie żeby otworzyć post
                            post_url = self.fb_notifications_url
                            full_content = preview
                            
                            try:
                                # Spróbuj kliknąć i przejść do posta
                                await notif.click(timeout=5000)
                                await asyncio.sleep(3)
                                
                                # Pobierz URL posta
                                post_url = page.url
                                
                                # Jeśli udało się przejść do posta, skanuj treść
                                if "groups" in post_url or "posts" in post_url:
                                    logger.info(f"   📍 Otwieram post: {post_url}")
                                    
                                    # Poczekaj na załadowanie treści posta
                                    await asyncio.sleep(2)
                                    
                                    # Spróbuj wyciągnąć pełną treść posta
                                    post_selectors = [
                                        'div[data-ad-preview="message"]',
                                        'div[data-ad-comet-preview="message"]',
                                        'div[dir="auto"]',
                                        'div.x11i5rnm'
                                    ]
                                    
                                    for post_selector in post_selectors:
                                        content_locator = page.locator(post_selector).first
                                        if await content_locator.count() > 0:
                                            full_content = await content_locator.inner_text(timeout=3000)
                                            logger.info(f"   ✅ Zeskanowano treść posta ({len(full_content)} znaków)")
                                            break
                                    
                                    # Wróć do powiadomień
                                    await page.goto(self.fb_notifications_url)
                                    await asyncio.sleep(2)
                                    
                            except Exception as e:
                                logger.debug(f"   ⚠️ Nie udało się otworzyć posta: {e}")
                                # Kontynuuj z preview
                            
                            # Wyślij na Discord
                            embed = discord.Embed(
                                title=f"🔵 Facebook - {group_name}", 
                                url=post_url, 
                                color=discord.Color.blue()
                            )
                            
                            # Ogranicz treść do 1000 znaków (limit Discord)
                            content_display = full_content[:1000]
                            if len(full_content) > 1000:
                                content_display += "..."
                            
                            embed.description = content_display
                            embed.add_field(name="Grupa", value=group_name, inline=False)
                            embed.set_footer(text="Facebook Group Notification")
                            
                            try:
                                await channel.send(embed=embed)
                                sent += 1
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
                logger.info(f"📈 PODSUMOWANIE FB: Sprawdzono={checked}, Wysłano={sent}, Pominięto: duplikaty={skipped_duplicate}, nieistotne={skipped_irrelevant}")
                
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
