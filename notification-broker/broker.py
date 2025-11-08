import asyncio
import websockets
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# GLOBAL REGISTER OF ACTIVE CONNECTIONS
# stores active WebSocket connections
ACTIVE_CONNECTIONS = {}

async def register_connection(websocket, user_id):
    """Rejestruje nowe połączenie i dodaje je do globalnego rejestru."""
    ACTIVE_CONNECTIONS[user_id] = websocket
    logger.info(f"User {user_id} connected. Active connections: {len(ACTIVE_CONNECTIONS)}")

async def unregister_connection(user_id):
    """Usuwa połączenie z rejestru po jego zamknięciu."""
    if user_id in ACTIVE_CONNECTIONS:
        del ACTIVE_CONNECTIONS[user_id]
        logger.info(f"User {user_id} disconnected. Active connections: {len(ACTIVE_CONNECTIONS)}")

async def consumer_handler(websocket, path):
    """
    Obsługuje wiadomości przychodzące od klienta (Frontend Vue).
    Front-end użyje tego do rejestracji swojego ID.
    """
    try:
        # 1. Nasłuchujemy pierwszej wiadomości (rejestracja)
        registration_message = await websocket.recv()
        data = json.loads(registration_message)
        
        # Oczekujemy, że klient Vue wyśle swoje 'user_id' na początku
        user_id = data.get('user_id')
        if not user_id:
            logger.error("Registration failed: 'user_id' missing in client message.")
            return

        await register_connection(websocket, user_id)

        # 2. Główna pętla nasłuchiwania
        # Utrzymujemy połączenie otwarte, aby mogło odbierać wiadomości od Brokera
        # lub od klienta (np. pingi). Wystarczy, że połączenie jest aktywne.
        # Ta pętla będzie trwała, dopóki połączenie nie zostanie przerwane.
        await websocket.wait_closed()

    finally:
        # Połączenie zamknięte - usuwamy użytkownika z rejestru
        if user_id:
            await unregister_connection(user_id)


async def producer_handler(websocket, path):
    """
    Obsługuje wiadomości przychodzące od serwisu Flask (Klienta).
    Serwis Flask łączy się, wysyła wiadomość i zamyka.
    """
    try:
        # Nasłuchujemy wiadomości z serwisu Flask
        message_from_flask = await websocket.recv()
        payload = json.loads(message_from_flask)
        
        target_user_id = payload.get('user_id')
        notification = payload.get('message')

        if target_user_id and target_user_id in ACTIVE_CONNECTIONS:
            target_websocket = ACTIVE_CONNECTIONS[target_user_id]
            
            # WYSŁANIE: Wypchnięcie wiadomości do front-endu
            await target_websocket.send(json.dumps(notification))
            logger.info(f"Notification PUSHED to user {target_user_id}: {notification['type']}") # <-- JEŚLI TO DZIAŁA, MUSI SIĘ ZALOGOWAĆ
            
            # Dodatkowe zabezpieczenie: Odsyłamy do Flask-a potwierdzenie
            await websocket.send(json.dumps({"status": "delivered"}))
        
        elif target_user_id:
            logger.warning(f"Notification skipped: User {target_user_id} is NOT CONNECTED.") 
            await websocket.send(json.dumps({"status": "user_offline"}))
        else:
            logger.error("Invalid payload from Flask: missing user_id.")

        # Opcjonalnie: odsyłamy do Flask-a potwierdzenie
        await websocket.send(json.dumps({"status": "delivered"}))

    except websockets.exceptions.ConnectionClosedOK:
        logger.info("Flask client disconnected normally.")
    except Exception as e:
        logger.error(f"Error handling Flask client message: {e}")


async def router_handler(websocket, *args, **kwargs):
    """
    Kieruje połączenia do odpowiedniego handlera na podstawie ścieżki URL.
    """
    
    path = '/'
    
    try:
        if len(args) > 0:
            path = args[0] # To jest najbardziej prawdopodobne miejsce, gdzie jest ścieżka
        elif 'path' in kwargs and kwargs['path'] is not None:
            path = kwargs['path']
            
    except Exception as e:
        logger.error(f"Failed to determine path: {e}")
        # W przypadku błędu path pozostaje '/'
        
    # KLUCZOWA POPRAWKA LOGICZNA: Jeśli path jest 'None' (co się dzieje), traktujemy to jako '/'.
    if path is None:
        path = '/' 

    logger.info(f"Incoming connection on path: {path}")

    # 2. Routing (Teraz wiemy, że 'path' nie jest None)
    if path == "/flask-push":
        await producer_handler(websocket, path) 
    
    elif path == "/":
        await consumer_handler(websocket, path)
    
    else:
        logger.warning(f"Connection refused for unknown path: {path}")
        await websocket.close(code=1000, reason="Invalid path")


async def main():
    """Główna funkcja uruchamiająca JEDEN serwer WebSocket."""
    # Uruchamiamy tylko JEDEN serwer i używamy router_handler do rozróżniania ścieżek
    server = websockets.serve(router_handler, "0.0.0.0", 8001)
    
    await server
    await asyncio.Future() # Trzyma serwer uruchomiony na zawsze
    
if __name__ == "__main__":
    logger.info("Starting Notification Broker on port 8001...")
    asyncio.run(main())