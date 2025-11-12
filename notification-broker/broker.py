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
    """
    Registers a new connection and 
    adds it to the global registry
    """

    ACTIVE_CONNECTIONS[user_id] = websocket
    logger.info(f"User {user_id} connected. Active connections: {len(ACTIVE_CONNECTIONS)}")

async def unregister_connection(user_id):
    """
    Removes the connection from the 
    registry after it is closed.
    """

    if user_id in ACTIVE_CONNECTIONS:
        del ACTIVE_CONNECTIONS[user_id]
        logger.info(f"User {user_id} disconnected. Active connections: {len(ACTIVE_CONNECTIONS)}")

async def consumer_handler(websocket, path):
    """
    Handles incoming messages from the client (Vue frontend)
    The frontend will use this to register its ID
    """
    try:
        # 1. listen to the first message (registration)
        registration_message = await websocket.recv()
        data = json.loads(registration_message)
        
        # expect the Vue client to send its ‘user_id’ at the beginning
        user_id = data.get('user_id')
        if not user_id:
            logger.error("Registration failed: 'user_id' missing in client message.")
            return

        await register_connection(websocket, user_id)

        # 2. Main listening loop
        # We keep the connection open so that it can receive messages from the Broker
        # or from the client (e.g., pings). It is sufficient for the connection to be active.
        # This loop will continue until the connection is terminated.
        await websocket.wait_closed()

    finally:
        # closed connection - we remove the user from the registry
        if user_id:
            await unregister_connection(user_id)

async def producer_handler(websocket, path):
    """
    Handles incoming messages from the Flask service (Client)
    The Flask service connects, sends a message, and closes
    """
    logger.info(f"FLASK CONNECTION RECEIVED on {path}.")
    try:
        # listen to messages from the Flask service
        message_from_flask = await websocket.recv()
        payload = json.loads(message_from_flask)
        
        target_user_id = payload.get('user_id')
        notification = payload.get('message')

        if target_user_id and target_user_id in ACTIVE_CONNECTIONS:
            target_websocket = ACTIVE_CONNECTIONS[target_user_id]
            
            # SENDING: Pushing messages to the front end
            await target_websocket.send(json.dumps(notification))
            logger.info(f"Notification PUSHED to user {target_user_id}: {notification['type']}")
            
            # Additional security:send confirmation to Flask
            await websocket.send(json.dumps({"status": "delivered"}))
        
        elif target_user_id:
            logger.warning(f"Notification skipped: User {target_user_id} is NOT CONNECTED.") 
            await websocket.send(json.dumps({"status": "user_offline"}))
        else:
            logger.error("Invalid payload from Flask: missing user_id.")

        # Optional: we refer to Flask for confirmation
        # await websocket.send(json.dumps({"status": "delivered"}))

    except websockets.exceptions.ConnectionClosedOK:
        logger.info("Flask client disconnected normally.")
    except Exception as e:
        logger.error(f"Error handling Flask client message: {e}")

async def router_handler(websocket, path):
    """
    It directs calls to the appropriate 
    handler based on the URL path
    """

    logger.info(f"Incoming connection on path: {path}")

    if path == "/flask-push":
        await producer_handler(websocket, path) 
    
    elif path == "/":
        await consumer_handler(websocket, path)
    
    else:
        logger.warning(f"Connection refused for unknown path: {path}")
        await websocket.close(code=1000, reason="Invalid path")

async def main():
    """
    The main function that starts 
    ONE WebSocket server
    """
    
    # start ONE server 
    # use router_handler to route between paths.
    server = websockets.serve(router_handler, "0.0.0.0", 8001)

    await server
    await asyncio.Future() # keeps server run forever

if __name__ == "__main__":
    logger.info("Starting Notification Broker on port 8001...")
    asyncio.run(main())