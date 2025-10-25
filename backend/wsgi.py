import os
from app import create_app

# ensure that secret keys are in docker environment 
# (injected in os.environ by docker compose)
os.environ['SECRET_KEY'] = os.environ.get(
    'SECRET_KEY', 
    'FALLBACK_SECRET_KEY')
os.environ['JWT_SECRET_KEY'] = os.environ.get(
    'JWT_SECRET_KEY', 
    'FALLBACK_JWT_SECRET_KEY')

app = create_app()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)