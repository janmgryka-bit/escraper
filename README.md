# 🚀 Janek Hunter v6.0 - Docker Edition

Bot do automatycznego skanowania ofert iPhone z OLX, Allegro Lokalnie i Facebook.

## 🐳 Uruchomienie z Dockerem (ZALECANE)

### Wymagania
- Docker
- Docker Compose
- Plik `.env` z tokenami

### Krok 1: Przygotuj plik `.env`

Stwórz plik `.env` w głównym folderze:

```env
DISCORD_TOKEN=twoj_token_discord
CHANNEL_ID=123456789
GROQ_API_KEY=twoj_klucz_groq
```

### Krok 2: Zbuduj i uruchom kontener

```bash
docker-compose up --build
```

Bot uruchomi się automatycznie i będzie działał w tle.

### Krok 3: Zatrzymanie bota

```bash
docker-compose down
```

### Krok 4: Sprawdzenie logów

```bash
docker-compose logs -f hunter-bot
```

## 📦 Trwałe dane (Persistent Volumes)

Docker automatycznie zapisuje:
- `fb_data/` - Sesja Facebook (nie musisz logować się ponownie)
- `hunter_final.db` - Baza danych z ofertami
- `scraper.log` - Logi bota

Dzięki temu nawet po restarcie kontenera bot pamięta wszystko.

## 🎮 Discord Commands

- `!start` - Uruchom skanowanie (z przyciskiem potwierdzenia)
- `!stop` - Zatrzymaj skanowanie
- `!set_budget 800` - Ustaw maksymalny budżet (zapisuje do config.yaml)
- `!status` - Sprawdź status bota

## ⚙️ Konfiguracja

Edytuj `config.yaml` aby zmienić:
- Modele iPhone do wyszukiwania
- Stany (uszkodzony, używany, nowy)
- Budżet maksymalny
- Interwały skanowania
- Ustawienia AI i Smart Matching

## 🔧 Uruchomienie bez Dockera (lokalnie)

```bash
# Zainstaluj zależności
pip install -r requirements.txt

# Zainstaluj przeglądarki Playwright
playwright install chromium

# Uruchom bota
python main.py
```

## 📊 Funkcje

✅ **Hash-based deduplication** - Unikalne ID z 100 znaków opisu + cena  
✅ **Pełny opis** - Discord embeds pokazują do 4000 znaków  
✅ **Discord commands** - Interaktywna kontrola przez Discord  
✅ **Persistent session** - Facebook nie wymaga ponownego logowania  
✅ **AI Analysis** - Groq AI ocenia stan telefonu ze zdjęć  
✅ **Smart Matching** - Inteligentne łączenie ofert (części + ekran)  
✅ **Profitability Calculator** - Automatyczna kalkulacja zysku  

## 🛡️ Jak uniknąć bana na Facebook

1. **Persistent session** - Docker mapuje `fb_data/` na dysk, więc sesja przetrwa restart
2. **Headless mode** - Bot działa w tle bez okna przeglądarki
3. **User-Agent** - Bot udaje normalną przeglądarkę Chrome
4. **Opóźnienia** - Randomowe interwały między skanowaniami

## 📝 Struktura projektu

```
escraper_v1/
├── Dockerfile              # Przepis na kontener
├── docker-compose.yml      # Konfiguracja Docker Compose
├── main.py                 # Główny plik bota
├── config.yaml             # Konfiguracja
├── requirements.txt        # Zależności Python
├── .env                    # Tokeny (NIE commituj!)
├── scrapers/
│   ├── olx_scraper.py      # Scraper OLX
│   ├── allegro_scraper.py  # Scraper Allegro Lokalnie
│   └── fb_scraper.py       # Scraper Facebook
└── utils/
    ├── database.py         # SQLite database
    ├── config_loader.py    # Ładowanie config.yaml
    ├── profitability.py    # Kalkulacja zysku
    └── ai_analyzer.py      # Groq AI analiza
```

## 🚨 Troubleshooting

**Bot nie startuje:**
- Sprawdź czy `.env` ma poprawne tokeny
- Sprawdź logi: `docker-compose logs -f`

**Facebook wymaga logowania:**
- Zaloguj się ręcznie w przeglądarce na tym samym komputerze
- Skopiuj cookies do `fb_data/`

**Duplikaty na Discord:**
- Bot używa hash z 100 znaków opisu + cena
- Jeśli ktoś zmieni opis, to będzie nowa oferta

## 📄 Licencja

MIT License - Janek Hunter v6.0
