# 🚀 Quick Start - System Konfiguracji

## ✅ Co zostało dodane?

### 1. **Plik konfiguracyjny `config.yaml`**
- ✅ Wybór modeli iPhone (15, 14, 13, 12, 11, SE)
- ✅ Filtry stanów (uszkodzony, zablokowany, używany, nowy)
- ✅ Cennik dla każdego modelu
- ✅ Widelki opłacalności (min zysk, max cena)
- ✅ Inteligentne łączenie ofert (2 uszkodzone = 1 sprawny)
- ✅ AI analiza (opcjonalne)

### 2. **Moduły Python**
- `utils/config_loader.py` - Ładowanie konfiguracji z YAML
- `utils/profitability.py` - Kalkulator opłacalności
- `utils/ai_analyzer.py` - AI do analizy ofert (opcjonalne)

### 3. **Dokumentacja**
- `CONFIG_GUIDE.md` - Pełny przewodnik (50+ przykładów)

---

## 🎯 Jak to działa?

### Przed (stary system):
```python
MAX_BUDGET = 500  # Hardcoded w kodzie
# Brak filtrów modeli
# Brak kalkulacji zysku
# Wysyła wszystko
```

### Teraz (nowy system):
```yaml
# config.yaml
models:
  enabled:
    - "iphone 15 pro"
    - "iphone 14 pro"
    
pricing:
  "iphone 15 pro":
    market_price: 4800
    buy_max_broken: 2500
    min_profit: 500
```

**Bot automatycznie:**
1. ✅ Sprawdza czy model jest na liście
2. ✅ Wykrywa stan (uszkodzony/sprawny/zablokowany)
3. ✅ Oblicza potencjalny zysk
4. ✅ Wysyła tylko jeśli opłacalne
5. ✅ Dodaje kalkulację do Discord embed

---

## 📊 Przykład działania

### Znaleziono ofertę: "iPhone 15 Pro rozbity ekran - 2400 zł"

**Krok 1: Wykrycie modelu**
```
Tytuł: "iPhone 15 Pro rozbity ekran"
Model: ✅ iphone 15 pro (na liście enabled)
```

**Krok 2: Wykrycie stanu**
```
Słowa kluczowe: "rozbity ekran"
Stan: uszkodzony
```

**Krok 3: Kalkulacja**
```yaml
# Z config.yaml:
market_price: 4800 zł
buy_max_broken: 2500 zł
repair_cost: 700 zł
min_profit: 500 zł
```

```
Cena zakupu: 2400 zł ✅ (< 2500 zł max)
Koszt naprawy: 700 zł
Koszt całkowity: 3100 zł
Cena sprzedaży: 4800 zł
ZYSK: 1700 zł ✅ (> 500 zł min)

Wynik: 🔥 SUPER OKAZJA!
```

**Krok 4: Discord Embed**
```
┌─────────────────────────────────┐
│ 🔥 SUPER OKAZJA                 │
│ iPhone 15 Pro                   │
├─────────────────────────────────┤
│ 💰 Cena: 2400 zł                │
│ 📊 Stan: Uszkodzony             │
│                                 │
│ 📈 KALKULACJA:                  │
│ • Zakup: 2400 zł                │
│ • Naprawa: 700 zł               │
│ • Razem: 3100 zł                │
│ • Sprzedaż: 4800 zł             │
│ • ZYSK: 1700 zł (35%)           │
│                                 │
│ ✅ Opłacalne! Zysk: 1700zł      │
└─────────────────────────────────┘
```

---

## 💡 Inteligentne Łączenie

Bot automatycznie znajduje pary ofert do połączenia!

### Przykład:

**Oferta 1:** iPhone 13 Pro, rozbity ekran, 1000 zł  
**Oferta 2:** iPhone 13 Pro, rozbita obudowa, 800 zł

**Kalkulacja:**
```
Zakup: 1000 + 800 = 1800 zł
Montaż: 550 zł
Razem: 2350 zł
Sprzedaż: 3000 zł
ZYSK: 650 zł ✅

Bot wysyła: 💡 Połącz 2 oferty! Zysk: 650 zł
```

---

## 🤖 AI Analiza (Opcjonalne)

Jeśli włączysz AI, bot dodatkowo:
- ✅ Ocenia stan telefonu (1-10)
- ✅ Wykrywa oszustwa
- ✅ Sugeruje czy warto kupić
- ✅ Dodaje uzasadnienie

### Jak włączyć:

1. Zarejestruj się: https://console.groq.com
2. Wygeneruj API key
3. Dodaj do `.env`:
   ```
   GROQ_API_KEY=gsk_twoj_klucz
   ```
4. W `config.yaml`:
   ```yaml
   ai:
     enabled: true
   ```

---

## 🎛️ Szybka Konfiguracja

### Scenariusz 1: Szukam tylko iPhone 15 Pro do naprawy

**Edytuj `config.yaml`:**
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

pricing:
  "iphone 15 pro":
    buy_max_broken: 3000
    min_profit: 600
```

### Scenariusz 2: Szukam sprawnych iPhone 13/14

```yaml
models:
  enabled:
    - "iphone 14 pro"
    - "iphone 13 pro"

conditions:
  uszkodzony: false
  uzywany: true
  nowy: true

pricing:
  "iphone 14 pro":
    buy_max_working: 3400
    min_profit: 400
```

### Scenariusz 3: Szukam par do łączenia

```yaml
models:
  enabled:
    - "iphone 13"
    - "iphone 12"

conditions:
  uszkodzony: true

smart_matching:
  enabled: true
  min_profit_combined: 500
```

---

## 📝 Następne Kroki

**UWAGA:** System jest gotowy, ale **jeszcze nie zintegrowany** z scraperami!

### Co trzeba zrobić:

1. ✅ Konfiguracja stworzona
2. ✅ Moduły napisane
3. ✅ Dokumentacja gotowa
4. ⏳ **Integracja z OLX scraper** (TODO)
5. ⏳ **Integracja z FB scraper** (TODO)
6. ⏳ **Testowanie** (TODO)

### Jak będzie działać po integracji:

```python
# main_refactored.py (po integracji)
from utils.config_loader import ConfigLoader
from utils.profitability import ProfitabilityCalculator

config = ConfigLoader('config.yaml')
profit_calc = ProfitabilityCalculator(config)

# W scraperze:
result = profit_calc.calculate(title, price, description)

if result['is_profitable']:
    # Wyślij na Discord z kalkulacją
    embed.add_field(name="Zysk", value=f"{result['potential_profit']}zł")
```

---

## 🎯 Podsumowanie

### Co masz teraz:

✅ **Plik config.yaml** - Wszystkie ustawienia w jednym miejscu  
✅ **Filtry modeli** - Wybierz które iPhone'y szukać  
✅ **Filtry stanów** - Uszkodzone, sprawne, zablokowane  
✅ **Cennik** - Dla każdego modelu osobno  
✅ **Kalkulator zysku** - Automatyczne obliczenia  
✅ **Smart matching** - Łączenie 2 ofert w 1  
✅ **AI analiza** - Opcjonalne, ale pomocne  
✅ **Dokumentacja** - 50+ przykładów w CONFIG_GUIDE.md  

### Co dalej:

⏳ Integracja z scraperami (następny krok)  
⏳ Testowanie systemu  
⏳ Dostrajanie cen i filtrów  

---

## 📚 Więcej Informacji

- **Pełny przewodnik:** `CONFIG_GUIDE.md`
- **Konfiguracja:** `config.yaml`
- **Przykłady:** Zobacz CONFIG_GUIDE.md sekcja "Przykłady Użycia"

**Wszystko gotowe do użycia!** 🚀

Następny krok: Zintegrować z scraperami i przetestować!
