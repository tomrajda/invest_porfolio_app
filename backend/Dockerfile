# KROK 1: use bazowego obrazu pythona
FROM python:3.10-slim

# KROK 2: set katalog roboczy wewnątrz kontenera
WORKDIR /app

# KROK 3: COPY plik z listą paczek do kontenera
COPY requirements.txt .

# KROK 4: INSTALL paczki 
RUN pip install --no-cache-dir -r requirements.txt 

# KROK 5: COPY resztę kodu aplikacji do kontenera
COPY . .

# KROK 6: Definicja portu, na którym nasłuchuje aplikacja
EXPOSE 5000

# KROK 7: Komenda uruchamiająca aplikację (już zdefiniowana w docker-compose, ale warto ją mieć)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "wsgi:app"]