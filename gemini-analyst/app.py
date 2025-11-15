import os
import json
import logging
import re
import json
from flask import Flask, request, jsonify

# WAŻNE: Musisz zainstalować te biblioteki w price-checker/requirements.txt też!
from google import genai
from google.genai.errors import APIError

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

# Konfiguracja API Gemini
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
    MODEL = 'gemini-2.5-flash'
else:
    logging.error("FATAL: GEMINI_API_KEY is not set.")
    client = None

# -----------------------------------------------------------
# GŁÓWNY ENDPOINT ANALIZY (Używany przez Flask)
# -----------------------------------------------------------
@app.route('/analyze-sentiment', methods=['POST'])
def analyze_sentiment():
    if not client:
        return jsonify({"msg": "Gemini service is not available."}), 503
        
    data = request.get_json()
    text_to_analyze = data.get('text')
    ticker = data.get('ticker', 'Unknown')
    
    if not text_to_analyze:
        return jsonify({"msg": "Text content for analysis is required."}), 400

    logging.info(f"Analyzing sentiment for {ticker}: {text_to_analyze[:50]}...")

    # Instrukcje dla modelu Gemini (Prompt Engineering)
    system_instruction = (
        "You are a specialized financial analyst. Analyze the following news headlines/article "
        "and determine the overall market sentiment. Respond ONLY with a single JSON object. "
        "The sentiment value MUST be one of: POSITIVE, NEGATIVE, or NEUTRAL. "
    )
    
    prompt = (
        f"Analyze this text related to {ticker}. Text: \"{text_to_analyze}\""
        "Format your output strictly as JSON: {\"sentiment\": \"[SENTIMENT_VALUE]\", \"summary\": \"[SHORT_10_WORD_SUMMARY]\"}"
    )

    try:
        # 1. Wywołanie API Gemini
        response = client.models.generate_content(
            model=MODEL,
            contents=[prompt],
            config=genai.types.GenerateContentConfig(
                system_instruction=system_instruction
            )
        )
        
        raw_text = response.text.strip()
        
        # --- KLUCZOWA ZMIANA: Użycie RegEx do wyodrębnienia czystego JSON ---
        
        # Wzór RegEx szuka pierwszego obiektu JSON {...} niezależnie od otaczających znaków
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        
        if not json_match:
            logging.error(f"Could not find JSON object in response: {raw_text}")
            return jsonify({"msg": "AI response was incomplete or not formatted as expected."}), 500
        
        # Używamy znalezionego, czystego ciągu JSON
        clean_json_string = json_match.group(0)

        # 2. Parsowanie odpowiedzi
        json_response = json.loads(clean_json_string) # Używamy czystego JSON
        
        return jsonify({
            "ticker": ticker,
            "sentiment": json_response.get("sentiment", "ERROR"),
            "summary": json_response.get("summary", "Could not parse summary.")
        }), 200

    except APIError as e:
        logging.error(f"Gemini API Call Failed: {e}")
        return jsonify({"msg": "AI API failed to process the request."}), 500
    except json.JSONDecodeError:
        logging.error(f"Gemini returned unparseable JSON: {raw_text}")
        return jsonify({"msg": "AI returned unparseable data."}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)