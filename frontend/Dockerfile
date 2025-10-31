# Używamy oficjalnego obrazu Node.js dla Vue.js
FROM node:lts-alpine

# Ustawiamy katalog roboczy
WORKDIR /app

# Kopiujemy pliki manifestu zależności i instalujemy je
COPY package*.json ./
RUN npm install

# Kopiujemy resztę kodu źródłowego
COPY . .

# Uruchamiamy serwer deweloperski
CMD ["npm", "run", "serve"]