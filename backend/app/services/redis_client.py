# app/services/redis_client.py
import redis
from app.config import settings


class FakeRedis:
    """In-memory fallback when Redis is unavailable."""

    def __init__(self):
        self._store = {}

    def get(self, key):
        import time
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if expires_at and time.time() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key, value, ex=None, nx=False):
        import time
        if nx and key in self._store:
            return False
        expires_at = (time.time() + ex) if ex else None
        self._store[key] = (value, expires_at)
        return True

    def delete(self, key):
        self._store.pop(key, None)

    def incr(self, key):
        entry = self._store.get(key)
        current = 0
        if entry:
            try:
                current = int(entry[0])
            except (ValueError, TypeError):
                current = 0
        new_val = current + 1
        self._store[key] = (str(new_val), None)
        return new_val

    def incrby(self, key, amount):
        entry = self._store.get(key)
        current = 0
        if entry:
            try:
                current = int(entry[0])
            except (ValueError, TypeError):
                current = 0
        new_val = current + int(amount)
        self._store[key] = (str(new_val), None)
        return new_val

    def expire(self, key, seconds):
        import time
        if key in self._store:
            value, _ = self._store[key]
            self._store[key] = (value, time.time() + seconds)
        return True

    def ping(self):
        return True


def _create_redis_client():
    try:
        # Prefer REDIS_URL if set (Railway provides this automatically)
        if settings.REDIS_URL:
            client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=2,
            )
        else:
            client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD or None,
                decode_responses=True,
                socket_connect_timeout=2,
            )
        client.ping()
        print("✅ Redis connected successfully")
        return client
    except Exception as e:
        print(f"⚠️ Redis unavailable, using in-memory fallback: {e}")
        return FakeRedis()


redis_client = _create_redis_client()
