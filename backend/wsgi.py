import os
from app import create_app

# ----------------------------------------------------
# Wymuszenie ustawienia kluczy w kontekście aplikacji
# Użyjemy wartości z os.environ, które są wstrzykiwane przez Docker Compose
# ----------------------------------------------------

# Zapewnij, że klucze są w zmiennych środowiskowych kontenera
os.environ['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'FALLBACK_SECRET_KEY')
os.environ['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'FALLBACK_JWT_SECRET_KEY')

app = create_app()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)