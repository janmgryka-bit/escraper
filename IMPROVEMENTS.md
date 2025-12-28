# 🎯 Proponowane Ulepszenia

## 1. **Webhook zamiast Bot Token** (Priorytet: WYSOKI)

### Dlaczego?
- Prostsze (nie trzeba zarządzać botem)
- Szybsze (bezpośrednie HTTP POST)
- Mniej zależności

### Jak zaimplementować:
```python
import requests
import os

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def send_discord_notification(title, url, price):
    embed = {
        "title": title,
        "url": url,
        "color": 5763719,  # green
        "fields": [
            {"name": "Cena", "value": f"**{price} zł**", "inline": True}
        ]
    }
    requests.post(WEBHOOK_URL, json={"embeds": [embed]})
```

## 2. **Retry Logic z Exponential Backoff** (Priorytet: ŚREDNI)

### Dlaczego?
- Obsługa tymczasowych błędów sieci
- Automatyczne ponowne próby
- Mniej false-negative

### Implementacja:
```bash
pip install tenacity
```

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def scrape_olx_with_retry(context, channel):
    return await olx_scraper.scrape(context, channel)
```

## 3. **Proper Logging** (Priorytet: WYSOKI)

### Dlaczego?
- Łatwiejsze debugowanie
- Historia działania bota
- Analiza problemów

### Implementacja:
```python
import logging
from logging.handlers import RotatingFileHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('scraper.log', maxBytes=10485760, backupCount=5),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info("Bot started")
logger.error(f"Error scraping: {e}")
```

## 4. **Docker Deployment** (Priorytet: ŚREDNI)

### Dlaczego?
- Łatwy deployment
- Izolowane środowisko
- Portable

### Dockerfile:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install --with-deps chromium

COPY . .

CMD ["python", "main_refactored.py"]
```

### docker-compose.yml:
```yaml
version: '3.8'
services:
  escraper:
    build: .
    env_file: .env
    volumes:
      - ./fb_data:/app/fb_data
      - ./hunter_final.db:/app/hunter_final.db
    restart: unless-stopped
```

## 5. **Health Check & Monitoring** (Priorytet: NISKI)

### Implementacja:
```python
from datetime import datetime

class HealthCheck:
    def __init__(self):
        self.last_successful_scrape = datetime.now()
        self.error_count = 0
    
    async def check_health(self, channel):
        time_since_last = (datetime.now() - self.last_successful_scrape).seconds
        if time_since_last > 600:  # 10 minut
            await channel.send("⚠️ Bot nie scrapował od 10 minut!")
```

## 6. **Rate Limiting** (Priorytet: WYSOKI)

### Dlaczego?
- Unikanie banów
- Mniej obciążenia serwerów
- Bardziej "ludzkie" zachowanie

### Implementacja:
```python
import time
from collections import deque

class RateLimiter:
    def __init__(self, max_requests=10, time_window=60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
    
    async def wait_if_needed(self):
        now = time.time()
        while self.requests and self.requests[0] < now - self.time_window:
            self.requests.popleft()
        
        if len(self.requests) >= self.max_requests:
            sleep_time = self.time_window - (now - self.requests[0])
            await asyncio.sleep(sleep_time)
        
        self.requests.append(now)
```

## 7. **Konfiguracja przez CLI** (Priorytet: NISKI)

### Implementacja:
```python
import argparse

parser = argparse.ArgumentParser(description='EScraper Bot')
parser.add_argument('--budget', type=int, default=500, help='Max budget')
parser.add_argument('--interval', type=int, default=180, help='Scrape interval')
parser.add_argument('--headless', action='store_true', help='Run headless')
args = parser.parse_args()
```

## 8. **Rozszerz o inne platformy** (Priorytet: ŚREDNI)

### Allegro:
```python
class AllegroScraper:
    async def scrape(self):
        url = "https://allegro.pl/listing?string=iphone&order=n"
        # Similar logic to OLX
```

### Vinted:
```python
class VintedScraper:
    async def scrape(self):
        url = "https://www.vinted.pl/catalog?search_text=iphone"
        # Similar logic
```

## 9. **Database Improvements** (Priorytet: NISKI)

### Dodaj więcej informacji:
```sql
CREATE TABLE offers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE,
    title TEXT,
    price INTEGER,
    platform TEXT,  -- 'olx', 'fb', 'allegro'
    location TEXT,
    seller_name TEXT,
    date_added TIMESTAMP,
    date_seen_last TIMESTAMP,
    times_seen INTEGER DEFAULT 1,
    notified BOOLEAN DEFAULT TRUE
)
```

## 10. **Testy Jednostkowe** (Priorytet: ŚREDNI)

### Struktura:
```
tests/
├── __init__.py
├── test_olx_scraper.py
├── test_fb_scraper.py
├── test_database.py
└── fixtures/
    └── sample_pages.html
```

### Przykład:
```python
import pytest
from scrapers.olx_scraper import OLXScraper

def test_price_extraction():
    scraper = OLXScraper(500, None)
    price = scraper.extract_price("1 200 zł")
    assert price == 1200

def test_old_model_filter():
    scraper = OLXScraper(500, None)
    assert scraper.is_old_model("iphone 7 plus")
    assert not scraper.is_old_model("iphone 13 pro")
```

## 🎯 Priorytetyzacja

### Must Have (Zrób teraz):
1. ✅ Napraw FB scraper (ZROBIONE)
2. ✅ Refactor kodu (ZROBIONE)
3. Dodaj proper logging
4. Dodaj rate limiting

### Should Have (Zrób wkrótce):
1. Webhook zamiast bot token
2. Retry logic
3. Docker deployment
4. Rozszerz o Allegro/Vinted

### Nice to Have (Opcjonalne):
1. Health monitoring
2. CLI configuration
3. Testy jednostkowe
4. Database improvements

## 📊 Szacowany czas implementacji

- Logging: 30 min
- Rate limiting: 1h
- Webhook: 30 min
- Retry logic: 30 min
- Docker: 1h
- Allegro scraper: 2h
- Testy: 3h
- Monitoring: 2h

**Total: ~10-12h dla wszystkich ulepszeń**
