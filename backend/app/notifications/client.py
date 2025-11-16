import asyncio
import websockets
import json
import os
import logging
import threading
import asyncio

logger = logging.getLogger(__name__)

# use service name in Docker Compose
NOTIFICATION_BROKER_URL = os.environ.get(
    'NOTIFICATION_BROKER_URL',
    'ws://notification-broker:8001/flask-push'
)

async def send_notification_async(user_id: str, message: dict):
    """
    sends an asynchronous notification 
    via WebSocket to the broker
    """
    payload = {
        'user_id': user_id,
        'message': message
    }
    
    uri = NOTIFICATION_BROKER_URL

    logger.info(f"Attempting to connect to broker at {uri}") # <-- NOWY LOG DEBUG

    try:

        async with websockets.connect(uri) as websocket:
            
            await websocket.send(json.dumps(payload))
            logger.info(f"Notification sent successfully: {payload}")
            
            return True
        
            # optional: wait on confirmation from Broker
            # response = await asyncio.wait_for(websocket.recv(), timeout=2)
            # logger.info(f"Broker response: {response}")

    except websockets.exceptions.ConnectionClosedOK:
        logger.warning(f"Connection to broker closed normally.")
    except Exception as e:
        logger.error(f"Failed to connect to or send data to Notification Broker: {e}")
        
        return False


def _start_async_loop_in_new_thread(coroutine):
    """Uruchamia podaną funkcję asynchroniczną w całkowicie nowym, izolowanym wątku."""
    
    def run_loop():
        try:
            # Tworzymy nową, czystą pętlę zdarzeń
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            # Uruchamiamy zadanie i czekamy na jego zakończenie
            loop.run_until_complete(coroutine)
        except Exception as e:
            logger.error(f"FAILURE IN ISOLATED THREAD: {e}")
        finally:
            # Kluczowe: Zamykamy pętlę, aby zapobiec wyciekom pamięci
            loop.close()

    # Uruchamiamy nowy wątek
    thread = threading.Thread(target=run_loop)
    thread.start()


def send_notification(user_id: str, message: dict):
    """
    Funkcja opakowująca dla kodu synchronicznego. Uruchamia WebSockets w tle.
    """
    logger.info(f"Notification request received for user {user_id}.")
    
    # Tworzymy zadanie asynchroniczne
    coroutine = send_notification_async(user_id, message)
    
    # Uruchamiamy je w osobnym, izolowanym wątku.
    _start_async_loop_in_new_thread(coroutine)


if __name__ == '__main__':
    send_notification(
        'test_user_123',
        {'type': 'TEST_MESSAGE', 'data': 'czesc z flaska!'}
    )