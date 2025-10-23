from app import create_app

# Tworzenie instancji aplikacji Flask
app = create_app()

if __name__ == "__main__":
    # Uruchomienie tylko w trybie deweloperskim
    app.run(host='0.0.0.0', port=5000)