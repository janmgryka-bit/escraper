# 🔵 Facebook Scraper - Przewodnik

## ✅ Co zostało naprawione?

### Poprzedni problem:
- ❌ Wysyłał te same powiadomienia wielokrotnie
- ❌ Nie wyciągał nazwy grupy
- ❌ Nie klikał w posty
- ❌ Pokazywał tylko preview, nie pełną treść

### Nowe rozwiązanie:
- ✅ **Baza danych** - śledzi już sprawdzone powiadomienia
- ✅ **Wyciąga nazwę grupy** - regex pattern matching
- ✅ **Klika w post** - otwiera pełną treść
- ✅ **Skanuje zawartość** - wyciąga pełny tekst posta
- ✅ **Unika duplikatów** - jak OLX, raz sprawdzone = nie wysyła ponownie

## 🎯 Jak działa?

### 1. Skanowanie powiadomień
```
🔔 Rozpoczynam sprawdzanie powiadomień FB...
✅ Strona FB notifications załadowana
✅ Znaleziono 12 powiadomień
```

### 2. Analiza każdego powiadomienia
```
Tekst: "Teraz w grupie iPhone Kupię / Sprzedam: „Sprzedam 15 pro Black titanium 128 GB 89% bateria...""

Wyciąga:
- Grupa: "iPhone Kupię / Sprzedam"
- Preview: "Sprzedam 15 pro Black titanium 128 GB 89% bateria..."
- ID: md5(grupa + preview) = "a3f2c1..."
```

### 3. Sprawdzenie w bazie
```sql
SELECT * FROM fb_notifications WHERE notification_id = 'a3f2c1...'
```

Jeśli **istnieje** → Pomija (duplikat)  
Jeśli **nie istnieje** → Kontynuuje

### 4. Kliknięcie w post
```
🎯 FB: Nowe powiadomienie! Grupa: iPhone Kupię / Sprzedam
   Preview: Sprzedam 15 pro Black titanium 128 GB...
   📍 Otwieram post: https://facebook.com/groups/123456/posts/789...
   ✅ Zeskanowano treść posta (456 znaków)
```

### 5. Wysyłka na Discord
```
Embed:
- Tytuł: "🔵 Facebook - iPhone Kupię / Sprzedam"
- URL: Link do posta
- Treść: Pełna zawartość posta (max 1000 znaków)
- Pole: Nazwa grupy
```

### 6. Zapis do bazy
```sql
INSERT INTO fb_notifications 
VALUES ('a3f2c1...', 'iPhone Kupię / Sprzedam', 'Pełna treść...', 'https://...', '2025-12-28 08:51:00')
```

## 📊 Przykładowe logi

### ✅ Znaleziono nowy post:
```
INFO - 🔔 Rozpoczynam sprawdzanie powiadomień FB...
INFO - ✅ Strona FB notifications załadowana
INFO - ✅ Znaleziono 8 powiadomień (selector: div[role="article"])
INFO - 🎯 FB: Nowe powiadomienie! Grupa: iPhone Kupię / Sprzedam
INFO -    Preview: Sprzedam 15 pro Black titanium 128 GB...
INFO -    📍 Otwieram post: https://facebook.com/groups/...
INFO -    ✅ Zeskanowano treść posta (456 znaków)
INFO - ✅ Wysłano powiadomienie FB: iPhone Kupię / Sprzedam
INFO - 📈 PODSUMOWANIE FB: Sprawdzono=8, Wysłano=1, Pominięto: duplikaty=5, nieistotne=2
```

### 🔄 Wszystko już było:
```
INFO - 🔔 Rozpoczynam sprawdzanie powiadomień FB...
INFO - ✅ Strona FB notifications załadowana
INFO - ✅ Znaleziono 8 powiadomień (selector: div[role="article"])
DEBUG - 🔄 Duplikat FB: iPhone Kupię / Sprzedam - Sprzedam 15 pro Black titanium...
DEBUG - 🔄 Duplikat FB: Skup Sprzedaż Telefonów - Witam...
INFO - 📈 PODSUMOWANIE FB: Sprawdzono=8, Wysłano=0, Pominięto: duplikaty=8, nieistotne=0
```

## 🔍 Wyciąganie nazwy grupy

### Obsługiwane formaty:
```
"Teraz w grupie iPhone Kupię / Sprzedam: „..."
→ Grupa: "iPhone Kupię / Sprzedam"

"w grupie Skup Sprzedaż Telefonów Sprawne i...: „..."
→ Grupa: "Skup Sprzedaż Telefonów Sprawne i..."

"group iPhone Buy/Sell: "..."
→ Grupa: "iPhone Buy/Sell"
```

### Regex patterns:
```python
r'w grupie ([^:]+):'      # Polski
r'w grupie ([^"]+)"'      # Polski z cudzysłowem
r'group ([^:]+):'         # Angielski
```

## 📝 Struktura bazy danych

### Tabela: `fb_notifications`
```sql
CREATE TABLE fb_notifications (
    notification_id TEXT PRIMARY KEY,  -- MD5 hash (grupa + preview)
    group_name TEXT,                   -- Nazwa grupy
    content TEXT,                      -- Pełna treść posta
    post_url TEXT,                     -- URL do posta
    date_added TEXT                    -- Timestamp
)
```

### Przykładowy rekord:
```
notification_id: "a3f2c1d4e5f6..."
group_name: "iPhone Kupię / Sprzedam"
content: "Sprzedam iPhone 15 Pro Black Titanium 128GB, stan idealny, bateria 89%..."
post_url: "https://facebook.com/groups/123456/posts/789..."
date_added: "2025-12-28T08:51:23.456789"
```

## 🎨 Discord Embed

```
┌─────────────────────────────────────────┐
│ 🔵 Facebook - iPhone Kupię / Sprzedam  │ ← Tytuł (klikalne)
├─────────────────────────────────────────┤
│ Sprzedam iPhone 15 Pro Black Titanium   │
│ 128GB, stan idealny, bateria 89%.       │
│ Cena: 4500 zł do negocjacji.            │ ← Pełna treść posta
│ Kontakt: 123-456-789                    │
│                                         │
│ Grupa: iPhone Kupię / Sprzedam         │ ← Pole z nazwą grupy
│                                         │
│ Facebook Group Notification             │ ← Footer
└─────────────────────────────────────────┘
```

## ⚙️ Konfiguracja

### Liczba sprawdzanych powiadomień:
```python
# W fb_scraper.py, linia ~100:
for i in range(min(count, 10)):  # Max 10 najnowszych
```

Zmień `10` na inną liczbę jeśli chcesz sprawdzać więcej/mniej.

### Filtrowanie po słowie kluczowym:
```python
# W fb_scraper.py, linia ~125:
if "iphone" not in text.lower():
    skipped_irrelevant += 1
    continue
```

Zmień `"iphone"` na inne słowo lub dodaj więcej warunków.

### Długość treści na Discord:
```python
# W fb_scraper.py, linia ~175:
content_display = full_content[:1000]  # Max 1000 znaków
```

Discord ma limit 2000 znaków dla description, ale 1000 jest bezpieczne.

## 🐛 Troubleshooting

### Problem: "Nie znaleziono powiadomień"
**Przyczyna:** Facebook zmienił strukturę DOM  
**Rozwiązanie:** Sprawdź logi, które selektory próbował:
```bash
grep "selector:" scraper.log
```

Możesz dodać nowe selektory w `fb_scraper.py`:
```python
notification_selectors = [
    'div[role="article"]',
    'div[role="listitem"]',
    'a[role="link"][href*="/groups/"]',
    'div.x1n2onr6',
    'TWOJ_NOWY_SELEKTOR'  # ← Dodaj tutaj
]
```

### Problem: "Sesja wygasła"
**Rozwiązanie:**
```bash
python fb_login.py
# Zaloguj się ręcznie w oknie przeglądarki
# Naciśnij ENTER gdy zalogowany
```

### Problem: Wysyła duplikaty
**Sprawdź bazę:**
```bash
sqlite3 hunter_final.db "SELECT COUNT(*) FROM fb_notifications"
```

Jeśli tabela nie istnieje, uruchom ponownie bota - automatycznie ją stworzy.

### Problem: Nie klika w posty
**Przyczyna:** Timeout lub zmiana struktury FB  
**Logi:**
```
⚠️ Nie udało się otworzyć posta: TimeoutError
```

Bot i tak wyśle preview, ale bez pełnej treści. To normalne dla niektórych powiadomień.

## 📈 Statystyki

### Sprawdź ile powiadomień FB w bazie:
```bash
sqlite3 hunter_final.db "SELECT COUNT(*) FROM fb_notifications"
```

### Zobacz ostatnie 5 powiadomień:
```bash
sqlite3 hunter_final.db "SELECT group_name, substr(content, 1, 50), date_added FROM fb_notifications ORDER BY date_added DESC LIMIT 5"
```

### Usuń wszystkie powiadomienia (reset):
```bash
sqlite3 hunter_final.db "DELETE FROM fb_notifications"
```

## 🔒 Bezpieczeństwo (unikanie bana)

### Co robi bot żeby nie dostać bana:

1. **Czeka 3-5 sekund** między akcjami
2. **Używa persistent context** - zachowuje sesję
3. **User agent** - wygląda jak prawdziwa przeglądarka
4. **Nie spamuje** - sprawdza max 10 powiadomień
5. **Losowe odstępy** - 2-4 minuty między cyklami
6. **Headless mode** - mniej podejrzane niż automation

### Dodatkowe zabezpieczenia (opcjonalne):

```python
# Losowe opóźnienia:
await asyncio.sleep(random.uniform(2, 5))

# Symuluj scroll:
await page.mouse.wheel(0, random.randint(100, 500))

# Ruch myszką:
await page.mouse.move(random.randint(100, 500), random.randint(100, 500))
```

## ✨ Następne kroki

Jeśli chcesz jeszcze bardziej ulepszyć:

1. **OCR dla zdjęć** - wyciągaj ceny ze screenshotów
2. **Marketplace** - pełna integracja z FB Marketplace
3. **Filtry** - tylko określone grupy, ceny, modele
4. **AI** - GPT do analizy czy oferta jest dobra
5. **Webhook** - szybsze powiadomienia niż bot

Wszystko działa! Teraz FB scraper jest równie dobry jak OLX scraper! 🎉
