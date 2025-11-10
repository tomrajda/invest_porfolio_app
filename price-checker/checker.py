import os
import requests
import asyncio
import websockets
import json
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import create_engine, text

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ENV CONFIGURATION
API_KEY = os.environ.get('FINNHUB_API_KEY', 'MOCK_KEY')
DATABASE_URL = os.environ.get('DATABASE_URL')
BROKER_URL = os.environ.get('NOTIFICATION_BROKER_URL', 'ws://notification-broker:8001/flask-push')
FINNHUB_URL = "https://finnhub.io/api/v1"

# Resources
engine = create_engine(DATABASE_URL) if DATABASE_URL else None
scheduler = AsyncIOScheduler()

async def push_notification_to_broker(user_id: str, message: dict):
    """
    Asynchronous sending of messages 
    to the Broker via WebSockets.
    """
    
    payload = {'user_id': user_id, 'message': message}
    
    try:
        # Timeout for no block Scheduler
        async with websockets.connect(BROKER_URL, open_timeout=5) as websocket: 
            await websocket.send(json.dumps(payload))
            logger.info(f"PUSHED Alert to Broker for user {user_id}")
            
    except Exception as e:
        logger.error(f"Failed to push alert to Broker: {e}")
        
def get_all_stocks_to_check():
    """
    Retrieves a list of unique symbols and 
    their owners from the database (synchronously).
    """

    if not engine:
        logger.error("No database configuration.")
        return []
        
    query = text("""
        SELECT DISTINCT s.ticker, p.user_id 
        FROM stock s JOIN portfolio p ON s.portfolio_id = p.id;
    """)
    
    try:
        with engine.connect() as connection:
            
            result = connection.execute(query).fetchall()

            # Convert result (ticker, user_id) on dictionary list
            return [{'ticker': r[0], 'user_id': str(r[1])} for r in result] 
        
    except Exception as e:
        logger.error(f"Database connection error while retrieving actions: {e}")
        return []

def get_current_price(ticker: str) -> float | None:
    """
    Get current prirce of a stock from Finnhub API
    """
    if not API_KEY:
        print("ERROR: FINNHUB_API_KEY is not set")
        return None

    url = f"{FINNHUB_URL}/quote?symbol={ticker}&token={API_KEY}"
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()

        data = response.json()
        
        # 'c' (current price) in Finnhub response
        current_price = data.get('c') 

        if current_price and current_price != 0:
            return float(current_price)
        else:
            print(f"Warning: Cannot find current price for {ticker}.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Communication error with Finnhub for {ticker}: {e}")
        return None

async def check_market_prices():
    """
    Scheduler's main task:
    checks prices and sends alerts.
    """

    logger.info("Market price verification has begun")
    
    stocks_to_check = get_all_stocks_to_check()
    
    # Dictionary for storing prices so that the API 
    # is not queried multiple times for the same symbol
    price_cache = {} 
    
    for stock in stocks_to_check:
        ticker = stock['ticker']
        user_id = stock['user_id']
        
        # 1. get the price (using cache or Finnhub)
        if ticker not in price_cache:
            price_cache[ticker] = get_current_price(ticker)
        
        current_price = price_cache[ticker]

        if current_price is not None and current_price > 0:
            
            # LOGIKA ALERTOWANIA 
            # wysylamy powiadomienie, jesli cena jest pow X

            #if current_price > 150:
            #     alert_message = {
            #        'type': 'PRICE_ALERT',
            #        'content': f"ALERT: {ticker} reached {current_price:.2f} USD!"
            #     }
            #     # 3. send an asynchronous notification
            #     await push_notification_to_broker(user_id, alert_message)
            
            update_message = {
                'type': 'PRICE_UPDATE',
                'ticker': ticker,
                'price': round(current_price, 2),
                'user_id': user_id
            }
            
            await push_notification_to_broker(user_id, update_message)

                 
    logger.info("Market price verification completed")

async def main_scheduler_loop():
    """
    An asynchronous function that starts 
    the scheduler and keeps it alive.
    """
    
    # 1. SCHEDULER start
    scheduler.start()
    logger.info("Scheduler started successfully and jobs are being monitored.")

    # 2. UMaintain event loop active
    try:
        while True:
            await asyncio.sleep(1) 
    except asyncio.CancelledError:
        logger.info("Scheduler loop cancelled.")
    finally:
        scheduler.shutdown()
        
if __name__ == '__main__':
    logger.info("Starting Price Checker Service...")

    # 1. Schedule job
    scheduler.add_job(check_market_prices, 'interval', seconds=30) 
    
    # 2. Run main asynchronous loop
    try:
        asyncio.run(main_scheduler_loop())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Price Checker Shutting Down...")