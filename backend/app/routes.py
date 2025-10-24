from flask import Blueprint, request, jsonify
from app import db, bcrypt, jwt
from app.models import User, Portfolio, Stock
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
# endpoint: create new portfolio
# -----------------------------------------------------------
@api.route('/portfolios', methods=['POST'])
@jwt_required()
def create_portfolio():
    # 1. get user ID from token JWT
    user_id = get_jwt_identity()
    
    # 2. get data from request
    data = request.get_json()
    name = data.get('name')

    if not name:
        return jsonify({"msg": "Portfolio name is required"}), 400

    # 3. check if portfolio with the same name already exists for this user
    existing_portfolio = Portfolio.query.filter_by(user_id=user_id, name=name).first()
    if existing_portfolio:
        return jsonify({"msg": "Portfolio with this name already exists"}), 409

    # 4. create and save new portfolio
    new_portfolio = Portfolio(name=name, user_id=user_id)
    
    db.session.add(new_portfolio)
    db.session.commit()
    
    # 5. success response
    return jsonify({
        "msg": "Portfolio created successfully",
        "id": new_portfolio.id,
        "name": new_portfolio.name
    }), 201

# -----------------------------------------------------------
# endpoint: test // get portfolios for logged-in user
# -----------------------------------------------------------
@api.route('/portfolios', methods=['GET'])
@jwt_required()
def get_portfolios():
    user_id = get_jwt_identity()
    
    portfolios = Portfolio.query.filter_by(user_id=user_id).all()
    
    # convert porfolios object to JSONs porfolios
    results = [{
        "id": p.id,
        "name": p.name
    } for p in portfolios]
    
    return jsonify(results), 200