import os
import redis

# connection with Redis (os env var of container)
REDIS_HOST = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CACHE_EXPIRATION = 60 * 60 * 24 # 24 godziny

try:
    redis_client = redis.from_url(REDIS_HOST)
    redis_client.ping()
    print("INFO: Connection to Redis established.")
except Exception as e:
    print(f"Error: Connection to Redis cannot be established: {e}")
    redis_client = None

def get_cache(key: str):
    """Get data from catche"""
    if redis_client:
        return redis_client.get(key)
    return None

def set_cache(key: str, value: str):
    """Sava data to catche with expiration date"""
    if redis_client:
        redis_client.setex(key, CACHE_EXPIRATION, value)
        return True
    return False