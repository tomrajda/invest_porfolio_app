import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager

# init extensions (bez przypisania do aplikacji)
db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
jwt = JWTManager()

def create_app(config_name=None):
    # create Flask app instance
    app = Flask(__name__)
    
    # -----------------------------------------------------------
    # 1. configure app
    # -----------------------------------------------------------
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')

    # configure CORS (allow front-end Vue for communication)
    CORS(app, resources={r"/api/*": {"origins": "*"}}) 

    # -----------------------------------------------------------
    # 2. init extenstions (przypisanie do aplikacji)
    # -----------------------------------------------------------
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # -----------------------------------------------------------
    # 3. register Blueprints (endpointów)
    # -----------------------------------------------------------
    from .routes import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')
    
    return app