# 🎛️ Przewodnik Konfiguracji - EScraper Advanced

## 📋 Spis Treści

1. [Podstawowa Konfiguracja](#podstawowa-konfiguracja)
2. [Modele iPhone](#modele-iphone)
3. [Stany Urządzeń](#stany-urządzeń)
4. [Cennik i Opłacalność](#cennik-i-opłacalność)
5. [Inteligentne Łączenie](#inteligentne-łączenie)
6. [AI Analiza](#ai-analiza)
7. [Przykłady Użycia](#przykłady-użycia)

---

## Podstawowa Konfiguracja

Plik: `config.yaml`

```yaml
general:
  max_budget: 500              # Maksymalny budżet (zł)
  check_interval_min: 120      # Min czas między skanami (s)
  check_interval_max: 240      # Max czas między skanami (s)
```

### Jak zmienić:

1. Otwórz `config.yaml`
2. Edytuj wartości
3. Zapisz plik
4. **Nie trzeba restartować bota!** (auto-reload)

---

## Modele iPhone

### Włączone modele (szukane):

```yaml
models:
  enabled:
    - "iphone 15 pro max"
    - "iphone 15 pro"
    - "iphone 14 pro"
    # ... dodaj więcej
```

### Wykluczone modele (pomijane):

```yaml
models:
  excluded:
    - "iphone x"
    - "iphone 8"
    - "iphone 7"
```

### Przykłady:

**Szukaj tylko iPhone 15:**
```yaml
enabled:
  - "iphone 15 pro max"
  - "iphone 15 pro"
  - "iphone 15 plus"
  - "iphone 15"
```

**Szukaj tylko Pro modeli:**
```yaml
enabled:
  - "iphone 15 pro max"
  - "iphone 15 pro"
  - "iphone 14 pro max"
  - "iphone 14 pro"
  - "iphone 13 pro max"
  - "iphone 13 pro"
```

---

## Stany Urządzeń

```yaml
conditions:
  uszkodzony: true      # Rozbity ekran, obudowa
  zablokowany: true     # Zablokowany iCloud
  uzywany: true         # Używany, sprawny
  nowy: true            # Nowy, nieużywany
  na_czesci: true       # Na części
```

### Co oznaczają:

- **uszkodzony** - Rozbity ekran, pęknięta obudowa, ale włącza się
- **zablokowany** - Activation Lock (iCloud), zwykle tylko na części
- **uzywany** - Sprawny, używany, bez uszkodzeń
- **nowy** - Nowy, nieużywany, w folii
- **na_czesci** - Nie włącza się, tylko na części

### Przykłady:

**Tylko sprawne telefony:**
```yaml
conditions:
  uszkodzony: false
  zablokowany: false
  uzywany: true
  nowy: true
  na_czesci: false
```

**Tylko uszkodzone (do naprawy):**
```yaml
conditions:
  uszkodzony: true
  zablokowany: false
  uzywany: false
  nowy: false
  na_czesci: true
```

---

## Cennik i Opłacalność

Dla każdego modelu definiujesz:

```yaml
pricing:
  "iphone 15 pro":
    market_price: 4800        # Cena rynkowa sprawnego
    buy_max_working: 4200     # Max cena zakupu sprawnego
    buy_max_broken: 2500      # Max cena zakupu uszkodzonego
    buy_max_locked: 1800      # Max cena zakupu zablokowanego
    repair_cost: 700          # Koszt naprawy (ekran + obudowa)
    unlock_cost: 0            # Koszt odblokowania (0 = niemożliwe)
    min_profit: 500           # Minimalny zysk
```

### Jak to działa:

**Przykład 1: Sprawny iPhone 15 Pro za 4000 zł**
```
Cena zakupu: 4000 zł
Koszt naprawy: 0 zł (sprawny)
Koszt całkowity: 4000 zł
Cena sprzedaży: 4800 zł
Zysk: 800 zł ✅ (min: 500 zł)
Wynik: OPŁACALNE!
```

**Przykład 2: Uszkodzony iPhone 15 Pro za 2300 zł**
```
Cena zakupu: 2300 zł
Koszt naprawy: 700 zł
Koszt całkowity: 3000 zł
Cena sprzedaży: 4800 zł
Zysk: 1800 zł ✅ (min: 500 zł)
Wynik: SUPER OKAZJA! 🔥
```

**Przykład 3: Uszkodzony iPhone 15 Pro za 2700 zł**
```
Cena zakupu: 2700 zł (> max 2500 zł)
Wynik: ZA DROGIE! ❌
```

### Jak ustawić własne ceny:

1. Sprawdź ceny rynkowe na OLX/Allegro
2. Ustal ile maksymalnie chcesz zapłacić
3. Oszacuj koszt naprawy (ekran ~400-800 zł)
4. Ustal minimalny zysk (np. 500 zł)

**Wzór:**
```
buy_max_broken = market_price - repair_cost - min_profit
```

Przykład dla iPhone 13:
```
market_price = 2400 zł
repair_cost = 500 zł
min_profit = 300 zł
buy_max_broken = 2400 - 500 - 300 = 1600 zł
```

---

## Inteligentne Łączenie

Bot automatycznie znajduje możliwości połączenia 2 uszkodzonych telefonów w 1 sprawny!

```yaml
smart_matching:
  enabled: true
  max_combined_cost: 0.85      # Max 85% ceny rynkowej
  min_profit_combined: 400     # Min zysk z połączenia
```

### Jak to działa:

**Przykład: iPhone 13 Pro**

Oferta 1:
- Cena: 1200 zł
- Stan: Rozbity ekran

Oferta 2:
- Cena: 900 zł
- Stan: Rozbita obudowa

**Kalkulacja:**
```
Koszt zakupu: 1200 + 900 = 2100 zł
Koszt naprawy: 550 zł (montaż)
Koszt całkowity: 2650 zł
Cena rynkowa: 3000 zł
Max dozwolony koszt: 3000 * 0.85 = 2550 zł

2650 > 2550 ❌ Nieopłacalne (za drogo)
```

**Lepszy przykład:**

Oferta 1: 1000 zł (rozbity ekran)
Oferta 2: 800 zł (rozbita obudowa)

```
Koszt całkowity: 1000 + 800 + 550 = 2350 zł
Max dozwolony: 2550 zł
Zysk: 3000 - 2350 = 650 zł ✅

Wynik: 💡 Połącz 2 oferty! Zysk: 650 zł
```

### Typy kombinacji:

1. **Ekran + Obudowa** - Jeden z rozbitym ekranem, drugi z rozbitą obudową
2. **iCloud + Uszkodzony** - Jeden zablokowany (na części), drugi uszkodzony
3. **2x Uszkodzone** - Dwa uszkodzone tego samego modelu

---

## AI Analiza

**OPCJONALNE** - Wymaga API key od Groq/OpenAI

```yaml
ai:
  enabled: false              # Włącz/wyłącz
  provider: "groq"            # groq, openai
  model: "llama-3.1-70b-versatile"
```

### Jak włączyć:

1. Zarejestruj się na https://console.groq.com
2. Wygeneruj API key
3. Dodaj do `.env`:
   ```
   GROQ_API_KEY=gsk_twoj_klucz_tutaj
   ```
4. W `config.yaml` ustaw `enabled: true`

### Co AI sprawdza:

- ✅ Czy oferta jest dobra
- ✅ Ocena stanu (1-10)
- ✅ Wykrywanie oszustw
- ✅ Szacowanie zysku
- ✅ Rekomendacja zakupu

### Przykład analizy AI:

```json
{
  "is_good_deal": true,
  "condition_score": 7,
  "is_scam": false,
  "estimated_profit": 850,
  "worth_buying": true,
  "ai_reasoning": "Telefon w dobrym stanie, cena poniżej rynkowej..."
}
```

---

## Przykłady Użycia

### Scenariusz 1: Szukam tylko iPhone 15 Pro do naprawy

```yaml
models:
  enabled:
    - "iphone 15 pro max"
    - "iphone 15 pro"

conditions:
  uszkodzony: true
  zablokowany: false
  uzywany: false
  nowy: false
  na_czesci: true

pricing:
  "iphone 15 pro":
    buy_max_broken: 3000
    min_profit: 600
```

### Scenariusz 2: Szukam sprawnych iPhone 13/14 do odsprzedaży

```yaml
models:
  enabled:
    - "iphone 14 pro"
    - "iphone 14"
    - "iphone 13 pro"
    - "iphone 13"

conditions:
  uszkodzony: false
  zablokowany: false
  uzywany: true
  nowy: true
  na_czesci: false

pricing:
  "iphone 14 pro":
    buy_max_working: 3400
    min_profit: 400
  "iphone 13 pro":
    buy_max_working: 2600
    min_profit: 300
```

### Scenariusz 3: Szukam par do łączenia (iPhone 12/13)

```yaml
models:
  enabled:
    - "iphone 13"
    - "iphone 12"

conditions:
  uszkodzony: true
  na_czesci: true

smart_matching:
  enabled: true
  max_combined_cost: 0.80    # Max 80% ceny
  min_profit_combined: 500   # Min 500 zł zysku

ai:
  enabled: true               # AI pomoże ocenić kombinacje
```

---

## Zaawansowane Opcje

### Discord Embedy

```yaml
discord:
  send_all: false              # false = tylko opłacalne
  send_ai_analysis: true       # Dodaj analizę AI
  send_profit_calc: true       # Dodaj kalkulację
  send_smart_matches: true     # Wysyłaj propozycje łączenia
```

### Kolory embedów:

```yaml
colors:
  profitable: 0x00ff00      # Zielony - opłacalne
  maybe: 0xffff00           # Żółty - może być
  not_profitable: 0xff0000  # Czerwony - nieopłacalne
  smart_match: 0x00ffff     # Cyan - połączenie
```

### Źródła danych:

```yaml
sources:
  olx: true
  facebook: true
  allegro: false    # TODO
  vinted: false     # TODO
```

---

## FAQ

**Q: Jak często bot sprawdza oferty?**  
A: Co 2-4 minuty (losowo), ustawiane w `check_interval_min/max`

**Q: Czy mogę mieć różne ceny dla różnych źródeł?**  
A: Nie, ceny są globalne dla wszystkich źródeł

**Q: Co jeśli zmienię config podczas działania bota?**  
A: Bot automatycznie przeładuje config przy następnym cyklu

**Q: Czy AI jest wymagane?**  
A: Nie, działa bez AI. AI to opcjonalne ulepszenie

**Q: Ile kosztuje API Groq?**  
A: Groq ma darmowy tier (30 req/min), wystarczy

**Q: Jak wyłączyć inteligentne łączenie?**  
A: Ustaw `smart_matching.enabled: false`

**Q: Czy mogę dodać własny model?**  
A: Tak, dodaj do `models.enabled` i `pricing`

**Q: Co jeśli nie ma cennika dla modelu?**  
A: Bot pominie ofertę z komunikatem "Brak cennika"

---

## Wskazówki

### 💡 Dobre praktyki:

1. **Zacznij od małego budżetu** - Przetestuj system
2. **Monitoruj logi** - Zobacz co bot znajduje
3. **Dostosuj ceny** - Po tygodniu sprawdź co się sprzedaje
4. **Włącz AI** - Pomoże uniknąć złych ofert
5. **Sprawdź smart matching** - Może znaleźć ukryte okazje

### ⚠️ Częste błędy:

1. **Za wysoki `buy_max_*`** - Kupisz za drogo, nie zarobisz
2. **Za niski `min_profit`** - Dużo pracy, mały zysk
3. **Wyłączone wszystkie `conditions`** - Bot nic nie znajdzie
4. **Brak modelu w `pricing`** - Oferty będą pomijane

### 🎯 Optymalizacja:

**Dla maksymalnego zysku:**
- Wysoki `min_profit` (500-800 zł)
- Niski `buy_max_*` (70-80% rynku)
- Włącz AI i smart matching

**Dla szybkiej rotacji:**
- Niższy `min_profit` (200-300 zł)
- Wyższy `buy_max_*` (85-90% rynku)
- Tylko sprawne telefony

---

## Przykładowy Embed na Discord

```
┌─────────────────────────────────────────┐
│ 🔥 SUPER OKAZJA - iPhone 15 Pro        │
├─────────────────────────────────────────┤
│ 💰 Cena: 2400 zł                        │
│ 📊 Stan: Uszkodzony (rozbity ekran)    │
│                                         │
│ 📈 KALKULACJA ZYSKU:                    │
│ • Koszt zakupu: 2400 zł                 │
│ • Koszt naprawy: 700 zł                 │
│ • Koszt całkowity: 3100 zł              │
│ • Cena rynkowa: 4800 zł                 │
│ • ZYSK: 1700 zł (35.4%)                 │
│                                         │
│ 🤖 AI ANALIZA:                          │
│ • Ocena stanu: 7/10                     │
│ • Oszustwo: Nie                         │
│ • Rekomendacja: KUP!                    │
│                                         │
│ 🔗 Link: https://olx.pl/...             │
└─────────────────────────────────────────┘
```

---

Gotowe! Teraz masz pełną kontrolę nad tym co bot szuka i jak ocenia opłacalność! 🚀
