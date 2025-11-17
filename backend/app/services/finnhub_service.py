import os
import requests
from .cache_service import get_cache, set_cache
from datetime import datetime, timedelta

FINNHUB_URL = "https://finnhub.io/api/v1"
API_KEY = os.environ.get('FINNHUB_API_KEY')

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

def get_company_metadata(ticker: str) -> dict | None:
    """ 
    Get company metadata from Finnhub API, including logo URL
    """
    CACHE_KEY = f"logo:{ticker}"
    
    # 1. Check CACHE
    cached_data = get_cache(CACHE_KEY)
    if cached_data:
        # Return logo from catche
        logo_url = cached_data.decode('utf-8')
        return {"logo": logo_url}

    if not API_KEY:
        print("BŁĄD: FINNHUB_API_KEY not set.")
        return None

    url = f"{FINNHUB_URL}/stock/profile2?symbol={ticker}&token={API_KEY}"
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()

        data = response.json()
           
        name = data.get('name')
        logo_url = data.get('logo')

        if logo_url:
            # CACHE save
            set_cache(CACHE_KEY, logo_url)

        return {
            "name": name,
            "logo": logo_url
        }

    except requests.exceptions.RequestException as e:
        print(f"Finnhub communciation error (metadata for {ticker}): {e}")
        return None

def get_recent_news_text(ticker: str, count: int = 5) -> str:
    """
    Retrieves the count of message headers for 
    a given symbol and combines them into a single text.
    """

    if not API_KEY:
        return "No Finnhub API key"

    # endpoint for retrieving news
    today = datetime.now().strftime('%Y-%m-%d')
    three_weeks_ago = (datetime.now() - timedelta(weeks=3)).strftime('%Y-%m-%d')

    url = f"{FINNHUB_URL}/company-news?symbol={ticker}&from={three_weeks_ago}&to={today}&token={API_KEY}"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        news_data = response.json()
        
        # Extracting headers from the first ‘count’ messages
        headlines = [item.get('headline') for item in news_data[:count] if item.get('headline')]
        
        if not headlines:
            return f"No news for {ticker}."
            
        # Combining headers into a single text that will be sent to Gemini
        return " | ".join(headlines)
        
    except requests.exceptions.RequestException as e:
        return f"Connectio Error with Finnhub (News): {e}"