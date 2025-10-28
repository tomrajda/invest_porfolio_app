import os
import requests

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
    if not API_KEY:
        print("BŁĄD: FINNHUB_API_KEY nie jest ustawiony.")
        return None

    url = f"{FINNHUB_URL}/stock/profile2?symbol={ticker}&token={API_KEY}"
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()

        data = response.json()
        
        return {
            "name": data.get('name'),
            "logo": data.get('logo') # <-- URL Logo
        }

    except requests.exceptions.RequestException as e:
        print(f"Finnhub communciation error (metadata for {ticker}): {e}")
        return None