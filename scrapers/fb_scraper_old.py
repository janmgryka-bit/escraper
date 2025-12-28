import asyncio
from datetime import datetime
import discord
import logging

logger = logging.getLogger('escraper.fb')

class FacebookScraper:
    def __init__(self):
        self.fb_notifications_url = "https://www.facebook.com/notifications"
        self.fb_marketplace_url = "https://www.facebook.com/marketplace/warsaw/search?query=iphone&exact=false"
    
    async def check_notifications(self, context, channel):
        """
        Check Facebook notifications for iPhone-related posts.
        
        KNOWN ISSUES:
        - Facebook's notification structure changes frequently
        - May require login session refresh
        - Selectors may need updating based on FB UI changes
        """
        page = await context.new_page()
        try:
            logger.info("🔔 Rozpoczynam sprawdzanie powiadomień FB...")
            print(f"🔔 [{datetime.now().strftime('%H:%M')}] Sprawdzam dzwoneczek FB...")
            await page.goto(self.fb_notifications_url, timeout=60000)
            logger.info("✅ Strona FB notifications załadowana")
            await asyncio.sleep(5)
            
            # Check if we're logged in
            login_check = await page.locator('input[name="email"]').count()
            if login_check > 0:
                logger.warning("⚠️ FB: Sesja wygasła! Wymagane ponowne logowanie")
                print("⚠️ FB: Sesja wygasła! Uruchom fb_login.py ponownie.")
                await channel.send("⚠️ **Facebook**: Sesja wygasła! Wymagane ponowne logowanie.")
                return
            
            # Try multiple selectors as Facebook changes them frequently
            notification_selectors = [
                'div[role="article"]',
                'div[role="gridcell"]',
                'div.x1n2onr6',
                'a[role="link"][href*="/notifications/"]'
            ]
            
            notifications_found = False
            for selector in notification_selectors:
                notif_locator = page.locator(selector)
                count = await notif_locator.count()
                
                if count > 0:
                    logger.info(f"✅ Znaleziono {count} powiadomień (selector: {selector})")
                    print(f"✅ Znaleziono {count} powiadomień (selector: {selector})")
                    notifications_found = True
                    
                    for i in range(min(count, 5)):
                        try:
                            notif = notif_locator.nth(i)
                            text = await notif.inner_text(timeout=5000)
                            
                            if "iphone" in text.lower():
                                logger.info(f"🎯 FB: Trafienie! Znaleziono iPhone w powiadomieniu")
                                print(f"🎯 FB: Trafienie! Znaleziono iPhone w powiadomieniu")
                                
                                embed = discord.Embed(
                                    title="🔵 NOWY POST NA FB - iPhone!", 
                                    url=self.fb_notifications_url, 
                                    color=discord.Color.blue()
                                )
                                embed.description = f"Treść: {text[:300]}..."
                                embed.set_footer(text="Sprawdź dzwoneczek na FB")
                                await channel.send(embed=embed)
                                logger.info("✅ Wysłano powiadomienie FB na Discord")
                                print("   ✅ Wysłano powiadomienie FB")
                                
                                # Try to click and get more details
                                try:
                                    await notif.click(timeout=3000)
                                    await asyncio.sleep(3)
                                    current_url = page.url
                                    if current_url != self.fb_notifications_url:
                                        print(f"   📍 URL posta: {current_url}")
                                except:
                                    pass
                                
                                await page.goto(self.fb_notifications_url)
                                await asyncio.sleep(2)
                        except Exception as e:
                            continue
                    break
            
            if not notifications_found:
                logger.warning("⚠️ FB: Nie znaleziono powiadomień (możliwe zmiany w strukturze FB)")
                print("⚠️ FB: Nie znaleziono powiadomień (możliwe zmiany w strukturze FB)")
                
        except Exception as e: 
            logger.error(f"❌ FB Error: {e}")
            print(f"❌ FB Error: {e}")
        finally: 
            await page.close()
    
    async def check_marketplace(self, context, channel):
        """
        Alternative: Check Facebook Marketplace directly for iPhone listings.
        More reliable than notifications.
        """
        page = await context.new_page()
        try:
            print(f"🛒 [{datetime.now().strftime('%H:%M')}] Sprawdzam FB Marketplace...")
            await page.goto(self.fb_marketplace_url, timeout=60000)
            await asyncio.sleep(5)
            
            # Check if logged in
            login_check = await page.locator('input[name="email"]').count()
            if login_check > 0:
                print("⚠️ FB Marketplace: Wymagane logowanie")
                return
            
            # Look for marketplace listings
            listing_selectors = [
                'a[href*="/marketplace/item/"]',
                'div[data-testid="marketplace_feed_item"]'
            ]
            
            for selector in listing_selectors:
                listings = await page.locator(selector).all()
                if len(listings) > 0:
                    print(f"✅ Znaleziono {len(listings)} ogłoszeń na Marketplace")
                    break
            
        except Exception as e:
            print(f"❌ FB Marketplace Error: {e}")
        finally:
            await page.close()
