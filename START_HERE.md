# 🚀 START HERE - Janek Hunter v6.0

## ✅ GOTOWE! Wszystko zintegrowane i działa!

### Test systemu:
```bash
# Test kalkulatora (już wykonany):
✅ Model: iphone 15 pro
✅ Zysk: 1700zł
✅ Opłacalne: True
✅ Rekomendacja: 🔥 SUPER OKAZJA! Zysk: 1700zł (35.4%)
```

---

## 🎯 Jak uruchomić:

### Opcja 1: Nowa wersja v6.0 (ZALECANE)
```bash
python main_v6.py
```

### Opcja 2: Stara wersja (backup)
```bash
python main_refactored.py
```

---

## 📝 Szybka konfiguracja:

### 1. Edytuj `config.yaml`:

**Wybierz modele:**
```yaml
models:
  enabled:
    - "iphone 15 pro"
    - "iphone 14 pro"
    - "iphone 13 pro"
```

**Wybierz stany:**
```yaml
conditions:
  uszkodzony: true      # Rozbite
  zablokowany: false    # iCloud lock
  uzywany: true         # Sprawne
  nowy: true            # Nowe
```

**Ustaw ceny (przykład dla iPhone 15 Pro):**
```yaml
pricing:
  "iphone 15 pro":
    market_price: 4800        # Cena rynkowa
    buy_max_broken: 2500      # Max za uszkodzony
    min_profit: 500           # Min zysk
```

### 2. Opcjonalnie: Włącz AI

```bash
# Dodaj do .env:
GROQ_API_KEY=gsk_twoj_klucz
```

```yaml
# W config.yaml:
ai:
  enabled: true
```

### 3. Uruchom:
```bash
python main_v6.py
```

---

## 🎨 Co zobaczysz na Discord:

### Przykład 1: Super okazja
```
┌─────────────────────────────────────┐
│ 🔥 IPHONE 15 PRO                    │ ← Zielony (opłacalne)
├─────────────────────────────────────┤
│ 💰 Cena: 2400 zł                    │
│ 📊 Stan: uszkodzony                 │
│                                     │
│ 📈 Kalkulacja:                      │
│ • Zakup: 2400 zł                    │
│ • Naprawa: 700 zł                   │
│ • Razem: 3100 zł                    │
│ • Sprzedaż: 4800 zł                 │
│ • ZYSK: 1700 zł (35.4%)             │
│                                     │
│ ✅ Ocena:                           │
│ 🔥 SUPER OKAZJA! Zysk: 1700zł       │
│                                     │
│ 🤖 AI Analiza: (jeśli włączone)    │
│ • Stan: 8/10                        │
│ • Warto: ✅ TAK                     │
│                                     │
│ ⚠️ Uszkodzenia: ekran               │
└─────────────────────────────────────┘
```

### Przykład 2: Smart Matching
```
┌─────────────────────────────────────┐
│ 💡 INTELIGENTNE POŁĄCZENIE          │ ← Cyan
│ IPHONE 13 PRO                       │
├─────────────────────────────────────┤
│ Typ: ekran + obudowa                │
│                                     │
│ 📱 Oferta 1:                        │
│ Cena: 1000 zł                       │
│ Stan: rozbity ekran                 │
│                                     │
│ 📱 Oferta 2:                        │
│ Cena: 800 zł                        │
│ Stan: rozbita obudowa               │
│                                     │
│ 📈 Kalkulacja:                      │
│ • Zakup: 1000 + 800 = 1800 zł       │
│ • Montaż: ~550 zł                   │
│ • Razem: 2350 zł                    │
│ • Sprzedaż: 3000 zł                 │
│ • ZYSK: 650 zł (21.7%)              │
│                                     │
│ ✅ Połącz 2 oferty! Zysk: 650zł     │
└─────────────────────────────────────┘
```

---

## 🔧 Co zostało dodane w v6.0:

### ✅ System konfiguracji
- Plik `config.yaml` - wszystkie ustawienia
- Filtry modeli i stanów
- Cennik dla każdego modelu
- Widelki opłacalności

### ✅ Kalkulator zysku
- Automatyczne wykrywanie modelu
- Wykrywanie stanu (uszkodzony/sprawny/zablokowany)
- Obliczanie potencjalnego zysku
- Ocena opłacalności

### ✅ Inteligentne łączenie
- Automatyczne znajdowanie par ofert
- 2 uszkodzone = 1 sprawny
- Kalkulacja opłacalności połączenia

### ✅ AI Analiza (opcjonalne)
- Ocena stanu (1-10)
- Wykrywanie oszustw
- Rekomendacje zakupu
- Uzasadnienie decyzji

### ✅ Ulepszone embedy Discord
- Kolorowe (zielony/żółty/czerwony/cyan)
- Pełna kalkulacja zysku
- AI analiza (jeśli włączone)
- Smart matching propozycje

---

## 📊 Logi w czasie rzeczywistym:

```
2025-12-28 09:20:15 - escraper - INFO - 🚀 Uruchamianie Janek Hunter v6.0...
2025-12-28 09:20:15 - escraper - INFO - 📝 Konfiguracja: config.yaml
2025-12-28 09:20:16 - escraper - INFO - ✅ Bot Discord zalogowany jako hunter#7598
2025-12-28 09:20:16 - escraper - INFO - 📱 Modele: iphone 15 pro max, iphone 15 pro... (19 total)
2025-12-28 09:20:16 - escraper - INFO - 📊 Stany: uszkodzony, zablokowany, uzywany, nowy
2025-12-28 09:20:16 - escraper - INFO - 🤖 AI: ❌ Wyłączone
2025-12-28 09:20:16 - escraper - INFO - 💡 Smart Matching: ✅ Włączone

============================================================
🔄 CYKL #1 - 2025-12-28 09:20:20
============================================================

2025-12-28 09:20:21 - escraper.olx - INFO - 🔍 Rozpoczynam skanowanie OLX...
2025-12-28 09:20:23 - escraper.olx - INFO - ✅ Strona OLX załadowana
2025-12-28 09:20:25 - escraper.olx - INFO - 📊 Znaleziono 48 ogłoszeń na stronie
2025-12-28 09:20:27 - escraper.olx - INFO - 🎯 ZNALEZIONO: iphone 15 pro rozbity ekran | 2400zł
2025-12-28 09:20:27 - escraper.olx - INFO -    🔥 SUPER OKAZJA! Zysk: 1700zł (35.4%)
2025-12-28 09:20:28 - escraper.olx - INFO - ✅ Wysłano na Discord
2025-12-28 09:20:30 - escraper.olx - INFO - 💡 Szukam inteligentnych połączeń...
2025-12-28 09:20:30 - escraper.olx - INFO - 💡 Wysłano smart match: iphone 13 pro | Zysk: 650zł
2025-12-28 09:20:30 - escraper.olx - INFO - 📈 PODSUMOWANIE OLX: Sprawdzono=25, Wysłano=3
```

---

## 🎛️ Dostosowanie:

### Zmień modele (tylko iPhone 15):
```yaml
models:
  enabled:
    - "iphone 15 pro max"
    - "iphone 15 pro"
    - "iphone 15 plus"
    - "iphone 15"
```

### Tylko uszkodzone (do naprawy):
```yaml
conditions:
  uszkodzony: true
  zablokowany: false
  uzywany: false
  nowy: false
  na_czesci: true
```

### Wyższy minimalny zysk:
```yaml
pricing:
  "iphone 15 pro":
    min_profit: 800  # Było: 500
```

### Wyłącz smart matching:
```yaml
smart_matching:
  enabled: false
```

---

## 📚 Dokumentacja:

- **`CONFIG_GUIDE.md`** - Pełny przewodnik (50+ przykładów)
- **`QUICK_START.md`** - Szybki start
- **`LOGGING_GUIDE.md`** - Przewodnik po logach
- **`FB_SCRAPER_GUIDE.md`** - Facebook scraper

---

## ⚡ Quick Tips:

1. **Edytuj config.yaml** - nie trzeba restartować bota (auto-reload co 10 cykli)
2. **Monitoruj logi** - `tail -f scraper.log`
3. **Testuj ceny** - Zobacz co się znajduje, dostosuj widelki
4. **Włącz AI** - Pomoże uniknąć złych ofert (wymaga Groq API key)
5. **Smart matching** - Może znaleźć ukryte okazje!

---

## 🐛 Troubleshooting:

**Problem:** Bot nic nie znajduje  
**Rozwiązanie:** Sprawdź `config.yaml` - czy modele są włączone, czy stany są true

**Problem:** Wszystko nieopłacalne  
**Rozwiązanie:** Zwiększ `buy_max_*` lub zmniejsz `min_profit` w config.yaml

**Problem:** Za dużo ofert  
**Rozwiązanie:** Zwiększ `min_profit` lub zmniejsz `buy_max_*`

**Problem:** AI nie działa  
**Rozwiązanie:** Sprawdź czy `GROQ_API_KEY` jest w `.env`

---

## 🎯 Wszystko gotowe!

```bash
python main_v6.py
```

**Enjoy! 🚀**
