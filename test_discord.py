#!/usr/bin/env python3
"""
Test Discord wysyłania - mockup data
"""
import asyncio
import discord
import os
from dotenv import load_dotenv

load_dotenv()

# Discord setup
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

# Import z config.py (tam jest hardcoded)
import sys
sys.path.insert(0, os.path.dirname(__file__))
from utils.config import CHANNEL_ID

@bot.event
async def on_ready():
    print(f"✅ Bot zalogowany: {bot.user}")
    
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print(f"❌ Nie znaleziono kanału: {CHANNEL_ID}")
        await bot.close()
        return
    
    print(f"✅ Kanał znaleziony: {channel.name}")
    
    # Test 1: Prosty tekst
    try:
        await channel.send("🧪 **TEST 1:** Prosty tekst działa!")
        print("✅ Test 1 OK")
    except Exception as e:
        print(f"❌ Test 1 FAIL: {e}")
    
    # Test 2: Embed
    try:
        embed = discord.Embed(
            title="🧪 TEST 2: Embed",
            url="https://www.olx.pl",
            color=0x00ff00,
            description="Test embeda z kolorami"
        )
        embed.add_field(name="💰 Cena", value="**500 zł**", inline=True)
        embed.add_field(name="📊 Stan", value="używany", inline=True)
        embed.set_footer(text="Test Footer")
        
        await channel.send(embed=embed)
        print("✅ Test 2 OK")
    except Exception as e:
        print(f"❌ Test 2 FAIL: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Mockup oferty OLX
    try:
        profit_result = {
            'model': 'iphone 11',
            'condition': 'używany',
            'buy_price': 500,
            'repair_cost': 0,
            'total_cost': 500,
            'market_price': 1500,
            'potential_profit': 1000,
            'profit_margin': 66.7,
            'is_profitable': True,
            'recommendation': '🔥 SUPER OKAZJA! Zysk: 1000zł (66.7%)',
            'damages': []
        }
        
        embed = discord.Embed(
            title=f"📱 {profit_result['model'].upper()}", 
            url="https://www.olx.pl/test", 
            color=0x00ff00,
            description="iPhone 11 64GB Biały - test mockup"
        )
        
        embed.add_field(name="💰 Cena", value=f"**{profit_result['buy_price']} zł**", inline=True)
        embed.add_field(name="📊 Stan", value=profit_result['condition'], inline=True)
        
        profit_text = (
            f"**Zakup:** {profit_result['buy_price']} zł\n"
            f"**Naprawa:** {profit_result['repair_cost']} zł\n"
            f"**Razem:** {profit_result['total_cost']} zł\n"
            f"**Sprzedaż:** {profit_result['market_price']} zł\n"
            f"**ZYSK:** {profit_result['potential_profit']} zł ({profit_result['profit_margin']:.1f}%)"
        )
        embed.add_field(name="📈 Kalkulacja", value=profit_text, inline=False)
        embed.add_field(name="✅ Ocena", value=profit_result['recommendation'], inline=False)
        embed.set_footer(text="OLX • Janek Hunter v6.0 TEST")
        
        await channel.send(embed=embed)
        print("✅ Test 3 OK - Mockup oferty wysłany!")
    except Exception as e:
        print(f"❌ Test 3 FAIL: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ Wszystkie testy zakończone!")
    await bot.close()

if __name__ == "__main__":
    TOKEN = os.getenv('DISCORD_TOKEN')
    if not TOKEN:
        print("❌ Brak DISCORD_TOKEN w .env")
        exit(1)
    
    print(f"🚀 Uruchamiam testy Discord...")
    print(f"📍 Channel ID: {CHANNEL_ID}")
    bot.run(TOKEN)
