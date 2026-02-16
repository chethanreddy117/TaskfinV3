import json
from app.services.redis_client import redis_client

STATE_TTL = 900        # 15 minutes default
HISTORY_TTL = 86400    # 24 hours


# ---------- TASK STATE ----------

def get_state(user_id: int) -> dict:
    """Get user's conversation state from Redis"""
    raw = redis_client.get(f"state:{user_id}")
    return json.loads(raw) if raw else {}


def set_state(user_id: int, state: dict, ttl: int = None) -> None:
    """
    Set user's conversation state in Redis.
    
    Args:
        user_id: User ID
        state: State dictionary to store
        ttl: Time-to-live in seconds (default: 900s / 15 minutes)
    """
    if ttl is None:
        ttl = STATE_TTL
    
    redis_client.set(
        f"state:{user_id}",
        json.dumps(state),
        ex=ttl
    )


def clear_state(user_id: int) -> None:
    """Clear user's conversation state"""
    redis_client.delete(f"state:{user_id}")


# ---------- CHAT HISTORY ----------

def get_chat_history(user_id: int) -> list:
    """Get chat history for a user"""
    raw = redis_client.get(f"conv:{user_id}")
    return json.loads(raw) if raw else []


def save_chat_history(user_id: int, history: list) -> None:
    """Save chat history for a user"""
    redis_client.set(
        f"conv:{user_id}",
        json.dumps(history),
        ex=HISTORY_TTL
    )


# ---------- DISTRIBUTED LOCKS ----------

def acquire_lock(lock_key: str, ttl: int = 30) -> bool:
    """
    Attempt to acquire a distributed lock.
    
    Args:
        lock_key: Unique lock identifier
        ttl: Lock expiry time in seconds
    
    Returns:
        True if lock acquired, False otherwise
    """
    return redis_client.set(lock_key, "1", ex=ttl, nx=True)


def release_lock(lock_key: str) -> None:
    """Release a distributed lock"""
    redis_client.delete(lock_key)
