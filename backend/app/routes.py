from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from app import db, bcrypt
from app.models import User, Portfolio, Stock
from app.notifications.client import send_notification_async, send_notification
from .services.finnhub_service import get_current_price, get_company_metadata, get_recent_news_text

from prometheus_client import Counter
import logging

import os
import asyncio
import requests
import threading

GEMINI_ANALYST_URL = os.environ.get('GEMINI_ANALYST_URL', 'http://gemini-analyst:5001')

# metrics for tracking failed login attempts
LOGIN_FAILURES = Counter(
    'app_login_failures_total', 
    'Failed login attempts number',
    ['reason']
)

# create Blueprint for API
api = Blueprint('api', __name__)

logger = logging.getLogger(__name__)

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
        if not user:
            LOGIN_FAILURES.labels(reason='user_not_found').inc()
        else:
            LOGIN_FAILURES.labels(reason='invalid_password').inc()
        
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
    

    message = f"Portfolio {name} created successfully."

    user_id = get_jwt_identity()
    notification_message = { 
        'type': 'PORTFOLIO_ADDED', 
        'content': message 
    }
    send_notification_async(user_id, notification_message) 

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

    message = f"Stock {ticker} added to portfolio {portfolio.name} successfully.",

    user_id = get_jwt_identity()
    notification_message = { 
        'type': 'STOCK_ADDED', 
        'content': message 
    }
    send_notification(user_id, notification_message) 
        
    return jsonify({
        "msg": message,
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

    message = f"Stock deleted from portfolio {portfolio.name} successfully."

    user_id = get_jwt_identity()
    notification_message = { 
        'type': 'STOCK_DELETED', 
        'content': message 
    }
    send_notification(user_id, notification_message) 

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

        message = f"Portfolio {portfolio.name} deleted successfully."

        user_id = get_jwt_identity()
        notification_message = { 
            'type': 'PORTFOLIO_DELETED', 
            'content': message 
        }
        send_notification(user_id, notification_message) 

        return jsonify({"msg": f"Portfolio '{portfolio_name}' and all associated stocks have been permanently deleted."}), 200

    except Exception as e:
        db.session.rollback()
        print(f"Database error during portfolio deletion: {e}")
        return jsonify({"msg": "An internal error occurred during deletion."}), 500

# -----------------------------------------------------------
# Logika Analizy AI (URUCHAMIANA W TLE PRZEZ SCHEDULER)
# -----------------------------------------------------------
async def analyze_and_notify(user_id: str, ticker: str, text_content: str):
    """Asynchronicznie wysyła tekst do serwisu Gemini i powiadamia użytkownika."""
    try:
        # 1. Wysyłka do serwisu Gemini Analyst (REST API)
        response = requests.post(
            f"{GEMINI_ANALYST_URL}/analyze-sentiment",
            json={"ticker": ticker, "text": text_content},
            timeout=30 # Długi timeout dla Gemini
        )
        response.raise_for_status()
        
        # 2. Odbiór wyniku
        result = response.json()
        sentiment = result.get('sentiment', 'N/A')
        
        # 3. Wysłanie powiadomienia do Brokera (WebSockets)
        notification_message = {
            'type': 'SENTIMENT_READY',
            'ticker': ticker,
            'sentiment': sentiment,
            'content': f"Twoja analiza nastrojów dla {ticker} jest gotowa: {sentiment}. Kliknij, aby zobaczyć wyniki."
        }
        # Zapewnij, że to jest czyste await
        success = await send_notification_async(user_id, notification_message)
        
        if success:
             logger.warning(f"AI NOTIFICATION SUCCESS: Sent ready status for {ticker}.")
        else:
             logger.error(f"AI NOTIFICATION FAILED: Could not push via broker for {ticker}.")

    except Exception as e:
        logger.error(f"AI Analysis Failed for {ticker}: {e}")

# -----------------------------------------------------------
# endpoint: triggers sentiment analysis
# -----------------------------------------------------------
@api.route('/stock/<string:ticker>/analyze', methods=['POST'])
@jwt_required()
def trigger_sentiment_analysis(ticker):
    user_id = get_jwt_identity()
    
    logger.error(f"--- TRIGGER RECEIVED for user {user_id} and ticker {ticker} ---") # LOG TESTOWY

    # 1. Pobranie tekstu z Finnhub (synchroniczne)
    news_text = get_recent_news_text(ticker)
    if "Błąd połączenia" in news_text or "Brak nowych wiadomości" in news_text:
        return jsonify({"msg": news_text}), 400

    # 2. Uruchomienie Asynchronicznej Analizy w TLE
    try:
        import threading # Zapewnij, że ten import jest na górze pliku
        
        # Funkcja opakowująca, która uruchamia asynchroniczne zadanie (analyze_and_notify)
        def start_analysis_in_thread():
            import asyncio
            # Używamy nowej, IZOLOWANEJ pętli w nowym wątku dla bezpieczeństwa
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(analyze_and_notify(user_id, ticker, news_text))
            loop.close()

        thread = threading.Thread(target=start_analysis_in_thread)
        thread.start()
        
    except Exception as e:
        logger.error(f"Could not start analysis thread: {e}")
        return jsonify({"msg": "Failed to start AI analysis process."}), 500

    # 3. Zwrócenie natychmiastowej odpowiedzi (202 Accepted)
    return jsonify({
        "msg": f"AI analysis for {ticker} started in the background. You will receive a notification."
    }), 202

@api.route('/stock/<string:ticker>/analyze/manual', methods=['POST'])
@jwt_required()
def trigger_manual_sentiment_analysis(ticker):
    """
    Uruchamia analizę AI w tle dla tekstu wprowadzonego przez użytkownika.
    """
    user_id = get_jwt_identity()
    data = request.get_json()
    text_content = data.get('text_content')
    
    if not text_content or len(text_content) < 50:
        return jsonify({"msg": "Text content must be at least 50 characters long for analysis."}), 400

    # 2. Uruchomienie Asynchronicznej Analizy w TLE (aby nie blokować REST API)
    # Tworzymy i uruchamiamy nowy wątek dla asynchronicznej funkcji analyze_and_notify
    try:
        # UWAGA: Użycie threading.Thread do uruchomienia asyncio.run(async_func) jest kluczowe 
        # w synchronicznym Flasku, aby uniknąć blokowania
        thread = threading.Thread(target=lambda: asyncio.run(analyze_and_notify(user_id, ticker, text_content)))
        thread.start()
    except Exception as e:
        logger.error(f"Could not start manual analysis thread: {e}")
        return jsonify({"msg": "Failed to start AI analysis process."}), 500

    return jsonify({"msg": f"AI analysis for {ticker} (manual input) started in the background. You will receive a notification."}), 202