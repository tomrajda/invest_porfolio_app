import asyncio
import websockets
import json
import os
import logging

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


def send_notification(user_id: str, message: dict):
    """
    Synchroniczne wywołanie asynchronicznej funkcji send_notification_async, 
    poprzez przekazanie zadania do aktywnej pętli zdarzeń.
    """
    try:
        # 1. Pobieramy bieżącą, aktywną pętlę zdarzeń (którą uruchomił Gunicorn)
        loop = asyncio.get_event_loop()
    except RuntimeError:
        # Jeśli pętla nie jest ustawiona (np. w testach), tworzymy nową
        loop = asyncio.get_event_loop_policy().new_event_loop()
        
    try:
        # 2. Przekazujemy asynchroniczną funkcję do wykonania w pętli.
        # run_coroutine_threadsafe jest idiomem do bezpiecznego przejścia sync->async
        future = asyncio.run_coroutine_threadsafe(
            send_notification_async(user_id, message),
            loop
        )
        # 3. Czekamy na wynik (z timeoutem), co symuluje operację synchroniczną
        future.result(timeout=5)
        
    except asyncio.TimeoutError:
        logger.error("Notification push timed out after 5s.")
    except Exception as e:
        logger.error(f"FAILURE: Cannot safely push notification via threadsafe: {e}")


if __name__ == '__main__':
    send_notification(
        'test_user_123',
        {'type': 'TEST_MESSAGE', 'data': 'czesc z flaska!'}
    )