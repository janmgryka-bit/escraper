# 📊 Przewodnik po Logowaniu

## Co się zmieniło?

Dodano **szczegółowe logowanie** - teraz widzisz dokładnie co bot robi w każdej chwili!

## Co zobaczysz w konsoli?

### Przy starcie:
```
2025-12-28 08:40:15 - escraper - INFO - ✅ Bot Discord zalogowany jako JanekHunter#1234
2025-12-28 08:40:15 - escraper - INFO - 📊 Konfiguracja: MAX_BUDGET=500zł, CHANNEL_ID=1454149554911051961
2025-12-28 08:40:15 - escraper - INFO - ✅ Połączono z kanałem Discord: okazje-iphone
2025-12-28 08:40:16 - escraper - INFO - 🌐 Uruchamianie przeglądarki Chromium...
2025-12-28 08:40:18 - escraper - INFO - ✅ Przeglądarka gotowa
```

### Podczas każdego cyklu:
```
============================================================
🔄 CYKL #1 - 2025-12-28 08:40:20
============================================================

🔔 Rozpoczynam sprawdzanie powiadomień FB...
✅ Strona FB notifications załadowana
⚠️ FB: Nie znaleziono powiadomień (możliwe zmiany w strukturze FB)

🔍 Rozpoczynam skanowanie OLX...
✅ Strona OLX załadowana
📊 Znaleziono 48 ogłoszeń na stronie
🚫 Pomijam stary model: iphone 8 plus 64gb
🎯 NOWA OKAZJA: iphone 11 64gb uszkodzony | 450zł
✅ Wysłano na Discord: iphone 11 64gb uszkodzony
📈 PODSUMOWANIE OLX: Sprawdzono=25, Wysłano=1, Pominięto: budżet=12, duplikaty=8, stare=3, brak_ceny=1

✅ Cykl #1 zakończony pomyślnie
💤 Czekam 187s do następnego cyklu...
```

## Pliki z logami

Wszystkie logi są zapisywane do pliku: **`scraper.log`**

```bash
# Zobacz ostatnie logi:
tail -f scraper.log

# Zobacz ostatnie 50 linii:
tail -n 50 scraper.log

# Szukaj błędów:
grep "ERROR" scraper.log

# Szukaj wysłanych ofert:
grep "Wysłano na Discord" scraper.log
```

## Co oznaczają ikony?

- 🔄 - Nowy cykl scrapowania
- 🔔 - Sprawdzanie Facebook
- 🔍 - Skanowanie OLX
- ✅ - Sukces
- ❌ - Błąd krytyczny
- ⚠️ - Ostrzeżenie
- 🎯 - Znaleziono okazję!
- 🚫 - Pominięto (stary model)
- 📊 - Statystyki
- 💤 - Czekanie

## Poziomy logowania

### INFO (domyślny)
Pokazuje wszystkie ważne wydarzenia:
- Start/stop bota
- Każdy cykl scrapowania
- Znalezione oferty
- Wysłane powiadomienia
- Podsumowania

### DEBUG (szczegółowy)
Dodaje więcej detali:
- Każdą pominiętą ofertę (za droga, duplikat)
- Szczegóły błędów
- Informacje techniczne

Aby włączyć DEBUG, edytuj `utils/logger.py`:
```python
logger.setLevel(logging.DEBUG)  # zamiast INFO
```

## Przykładowe logi

### ✅ Wszystko działa:
```
INFO - 🔍 Rozpoczynam skanowanie OLX...
INFO - ✅ Strona OLX załadowana
INFO - 📊 Znaleziono 48 ogłoszeń na stronie
INFO - 🎯 NOWA OKAZJA: iphone 12 mini | 480zł
INFO - ✅ Wysłano na Discord: iphone 12 mini
INFO - 📈 PODSUMOWANIE OLX: Sprawdzono=25, Wysłano=1
INFO - ✅ Cykl #1 zakończony pomyślnie
```

### ⚠️ FB sesja wygasła:
```
INFO - 🔔 Rozpoczynam sprawdzanie powiadomień FB...
INFO - ✅ Strona FB notifications załadowana
WARNING - ⚠️ FB: Sesja wygasła! Wymagane ponowne logowanie
```
**Rozwiązanie:** Uruchom `python fb_login.py`

### ❌ Błąd połączenia:
```
ERROR - ❌ OLX Global Error: TimeoutError: page.goto: Timeout 30000ms exceeded
```
**Rozwiązanie:** Sprawdź połączenie internetowe, bot spróbuje ponownie w następnym cyklu

### 📊 Brak nowych ofert:
```
INFO - 📈 PODSUMOWANIE OLX: Sprawdzono=25, Wysłano=0, Pominięto: budżet=15, duplikaty=10, stare=0, brak_ceny=0
```
To normalne - znaczy że nie ma nowych okazji w tym cyklu.

## Analiza logów

### Ile ofert wysłano dzisiaj?
```bash
grep "$(date +%Y-%m-%d)" scraper.log | grep "Wysłano na Discord" | wc -l
```

### Jakie były ostatnie błędy?
```bash
grep "ERROR" scraper.log | tail -n 10
```

### Statystyki z ostatniego cyklu:
```bash
grep "PODSUMOWANIE OLX" scraper.log | tail -n 1
```

### Kiedy bot ostatnio działał?
```bash
tail -n 1 scraper.log
```

## Rotacja logów

Logi automatycznie się rotują:
- Maksymalny rozmiar: **10MB**
- Liczba backupów: **5**
- Stare logi: `scraper.log.1`, `scraper.log.2`, itd.

## Monitorowanie w czasie rzeczywistym

```bash
# Otwórz terminal i uruchom:
tail -f scraper.log

# Lub tylko ważne rzeczy:
tail -f scraper.log | grep -E "(OKAZJA|Wysłano|ERROR|Cykl #)"
```

## FAQ

**Q: Dlaczego widzę "Sprawdzono=25" ale jest 48 ogłoszeń?**  
A: Bot sprawdza tylko top 25 najnowszych ofert (ustawienie w kodzie).

**Q: Co oznacza "duplikaty=10"?**  
A: Bot już widział te oferty wcześniej i są w bazie danych.

**Q: Czy mogę wyłączyć logi?**  
A: Nie zalecane, ale możesz zmienić poziom na `WARNING` w `utils/logger.py`.

**Q: Gdzie są logi z poprzednich dni?**  
A: W plikach `scraper.log.1`, `scraper.log.2`, itd.
