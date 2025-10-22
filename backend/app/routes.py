from flask import Blueprint, request, jsonify
from app import db, bcrypt, jwt
from app.models import User
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

# create Blueprint for API
api = Blueprint('api', __name__)

# -----------------------------------------------------------
# endpoint: register new user
# -----------------------------------------------------------
@api.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"msg": "Missing username or password"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"msg": "User already exists"}), 409

    # hash the password before saving to database
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    
    new_user = User(username=username, password_hash=hashed_password)
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"msg": "User created successfully"}), 201

# -----------------------------------------------------------
# endpoint: user login
# -----------------------------------------------------------
@api.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    # verify password and user existence
    if user and bcrypt.check_password_hash(user.password_hash, password):
        # generate token JWT (dane, które będą w tokenie to id użytkownika)
        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({"msg": "Bad username or password"}), 401

# -----------------------------------------------------------
# endpoint: test (login required)
# -----------------------------------------------------------
@api.route('/protected', methods=['GET'])
@jwt_required() #dekorator wymagający podania tokenu JWT
def protected():
    # Pobranie id użytkownika z tokenu
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    return jsonify(logged_in_as=user.username), 200