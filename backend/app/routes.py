from flask import Blueprint, request, jsonify
from app import db, bcrypt, jwt
from app.models import User, Portfolio, Stock
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from .services.finnhub_service import get_current_price, get_company_metadata

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
        access_token = create_access_token(identity=str(user.id))
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
    try:
        user_id = int(get_jwt_identity()) 
    except ValueError:
        return jsonify({"msg": "Invalid token subject type"}), 400
    
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
# endpoint: get all portfolios for user
# -----------------------------------------------------------
@api.route('/portfolios', methods=['GET'])
@jwt_required()
def get_portfolios():
    # 1. get user ID from token JWT
    try:
        user_id = int(get_jwt_identity()) 
    except ValueError:
        return jsonify({"msg": "Invalid token subject type"}), 400
    
    portfolios = Portfolio.query.filter_by(user_id=user_id).all()
    
    # conversion of Portfolio objects to JSON
    results = [{
        "id": p.id,
        "name": p.name
    } for p in portfolios]
    
    return jsonify(results), 200

# -----------------------------------------------------------
# endpoint: add new stock to portfolio
# -----------------------------------------------------------
@api.route('/portfolios/<int:portfolio_id>/stocks', methods=['POST'])
@jwt_required()
def add_stock_to_portfolio(portfolio_id):
    # 1. get user ID from token JWT
    try:
        user_id = int(get_jwt_identity()) 
    except ValueError:
        return jsonify({"msg": "Invalid token subject type"}), 400
    
    # 2. get data from request
    data = request.get_json()

    portfolio = Portfolio.query.get(portfolio_id)

    # check if portfolio exists and belongs to user
    if not portfolio or portfolio.user_id != user_id:
        return jsonify({"msg": "Portfolio not found or access denied"}), 404

    # 3. input data validation
    try:
        ticker = data.get('ticker').upper()
        shares = float(data.get('shares'))
        purchase_price = float(data.get('purchase_price'))
    except (ValueError, AttributeError):
        return jsonify({"msg": "Invalid data format (ticker, shares, or price)"}), 400

    if not ticker or shares <= 0 or purchase_price <= 0:
        return jsonify({"msg": "Invalid input: Ticker, shares and purchase price are required and must be positive."}), 400

    # 4. create and save new stock
    new_stock = Stock(
        ticker=ticker,
        shares=shares,
        purchase_price=purchase_price,
        portfolio_id=portfolio.id
    )

    db.session.add(new_stock)
    db.session.commit()

    return jsonify({
        "msg": f"Stock {ticker} added to portfolio {portfolio.name} successfully.",
        "stock_id": new_stock.id,
        "ticker": new_stock.ticker
    }), 201

# -----------------------------------------------------------
# endpoint: download full porfolio with stock prices
# -----------------------------------------------------------
@api.route('/portfolios/<int:portfolio_id>/valuation', methods=['GET']) # <-- NOWY URL!
@jwt_required()
def get_full_portfolio_valuation(portfolio_id):
    # 1. get user ID from token JWT
    try:
        user_id = int(get_jwt_identity()) 
    except ValueError:
        return jsonify({"msg": "Invalid token subject type"}), 400
    
    portfolio = Portfolio.query.get(portfolio_id)

    if not portfolio or portfolio.user_id != user_id:
        return jsonify({"msg": "Portfolio not found or access denied"}), 404

    total_market_value = 0.0
    stocks_with_valuation = []
    # Create dictionary to not load many times
    # (aby nie pytac API wielokrotnie o ten sam ticker)
    ticker_metadata_cache = {}

    stocks = Stock.query.filter_by(portfolio_id=portfolio.id).all()

    for stock in stocks:
        ticker = stock.ticker
        
        # check if metadata is laredy in cachce
        if ticker not in ticker_metadata_cache:
             ticker_metadata_cache[ticker] = get_company_metadata(ticker)
             
        metadata = ticker_metadata_cache[ticker] or {}

        current_price = get_current_price(ticker)
        
        market_value = 0.0
        profit_loss = 0.0
        
        if current_price is not None:
            market_value = current_price * float(stock.shares)
            initial_value = float(stock.purchase_price) * float(stock.shares)
            profit_loss = market_value - initial_value
            total_market_value += market_value

        stocks_with_valuation.append({
            "id": stock.id,
            "ticker": stock.ticker,
            "shares": str(stock.shares),
            "purchase_price": str(stock.purchase_price),
            "current_price": current_price,
            "market_value": round(market_value, 2),
            "profit_loss": round(profit_loss, 2),
            "logo_url": metadata.get('logo'),
            "company_name": metadata.get('name'),
        })

    return jsonify({
        "portfolio_name": portfolio.name,
        "stocks": stocks_with_valuation,
        "total_market_value": round(total_market_value, 2)
    }), 200

# -----------------------------------------------------------
# endpoint: remove shares from porfolio (DELETE)
# -----------------------------------------------------------
@api.route('/portfolios/<int:portfolio_id>/stocks/<int:stock_id>', methods=['DELETE'])
@jwt_required()
def delete_stock_from_portfolio(portfolio_id, stock_id):
    # 1. get user ID from token JWT
    try:
        user_id = int(get_jwt_identity()) 
    except ValueError:
        return jsonify({"msg": "Invalid token subject type"}), 400
    
    # 1. verify stock and its ownership
    stock = Stock.query.filter_by(id=stock_id, portfolio_id=portfolio_id).first()
    
    if not stock:
        return jsonify({"msg": "Stock not found in this portfolio."}), 404
        
    # 2. verify portfolio ownership
    portfolio = Portfolio.query.get(portfolio_id)
    if not portfolio or portfolio.user_id != user_id:
        return jsonify({"msg": "Access denied to this portfolio."}), 403

    # 3. delete stock
    db.session.delete(stock)
    db.session.commit()

    return jsonify({"msg": f"Stock {stock.ticker} (ID: {stock_id}) successfully removed."}), 200

@api.route('/portfolios/<int:portfolio_id>', methods=['DELETE'])
@jwt_required()
def delete_portfolio(portfolio_id):
    # 1. get user ID from token JWT
    try:
        user_id = int(get_jwt_identity()) 
    except ValueError:
        return jsonify({"msg": "Invalid token subject type"}), 400
    
    portfolio = Portfolio.query.get(portfolio_id)

    # 2. check permissions
    if not portfolio or portfolio.user_id != user_id:
        return jsonify({"msg": "Portfolio not found or access denied."}), 404

    portfolio_name = portfolio.name
    
    try:
        # 2. delete portfolio (delete all associated stocks 
        # will be deleted thanks to model)
        db.session.delete(portfolio)
        db.session.commit()

        return jsonify({"msg": f"Portfolio '{portfolio_name}' and all associated stocks have been permanently deleted."}), 200

    except Exception as e:
        db.session.rollback()
        print(f"Database error during portfolio deletion: {e}")
        return jsonify({"msg": "An internal error occurred during deletion."}), 500