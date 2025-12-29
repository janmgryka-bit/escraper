# Używamy oficjalnego obrazu Playwright - ma wszystkie przeglądarki wgrane
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# Kopiujemy wymagania i instalujemy
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiujemy resztę kodu
COPY . .

# Flaga, żeby Python nie buforował logów (widzisz wszystko na bieżąco)
ENV PYTHONUNBUFFERED=1

# Odpalamy bota
CMD ["python", "main.py"]
