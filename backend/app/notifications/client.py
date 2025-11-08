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

            # optional: wait on confirmation from Broker
            # response = await asyncio.wait_for(websocket.recv(), timeout=2)
            # logger.info(f"Broker response: {response}")

    except websockets.exceptions.ConnectionClosedOK:
        logger.warning(f"Connection to broker closed normally.")
    except Exception as e:
        logger.error(f"Failed to connect to or send data to Notification Broker: {e}")

def send_notification(user_id: str, message: dict):
    """
    Wrapper function for synchronous code (e.g., Flask routes).
    Runs an asynchronous function in a separate thread (loop).
    """
    try:
        asyncio.run(send_notification_async(user_id, message))
    except Exception as e:
        logger.error(f"Failed to run asyncio loop for notification: {e}")


if __name__ == '__main__':
    send_notification(
        'test_user_123',
        {'type': 'TEST_MESSAGE', 'data': 'czesc z flaska!'}
    )