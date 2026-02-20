import redis
import json
import time

import json
import time

from app.services.redis_client import redis_client
MONTH = 30 * 24 * 60 * 60


def add_recurring(user_id: str, bill: str, amount: int):
    rule = {
    "bill": bill,
    "amount": amount,
    "interval": "monthly",
    "status": "ACTIVE",        # NEW
    "next_run": int(time.time()) + MONTH,
    "created_at": int(time.time()),
    }


    redis_client.hset(
        f"user:{user_id}:recurring",
        bill,
        json.dumps(rule),
    )


def get_recurring(user_id: str):
    raw = redis_client.hgetall(f"user:{user_id}:recurring")
    return [json.loads(v) for v in raw.values()]


def get_all_recurring():
    """
    Returns all recurring rules grouped by user_id.
    {
        user_id: [rule, rule, ...]
    }
    """
    keys = redis_client.keys("user:*:recurring")
    result = {}

    for key in keys:
        user_id = key.split(":")[1]
        raw = redis_client.hgetall(key)
        result[user_id] = [json.loads(v) for v in raw.values()]

    return result


def update_recurring(user_id: str, rule: dict):
    """
    Update an existing recurring rule after execution
    (e.g. update next_run, last_run, status)
    """
    redis_client.hset(
        f"user:{user_id}:recurring",
        rule["bill"],
        json.dumps(rule),
    )

def pause_recurring(user_id: str, bill: str) -> bool:
    key = f"user:{user_id}:recurring"
    raw = redis_client.hget(key, bill)
    if not raw:
        return False

    rule = json.loads(raw)
    rule["status"] = "PAUSED"
    redis_client.hset(key, bill, json.dumps(rule))
    return True


def resume_recurring(user_id: str, bill: str) -> bool:
    key = f"user:{user_id}:recurring"
    raw = redis_client.hget(key, bill)
    if not raw:
        return False

    rule = json.loads(raw)
    rule["status"] = "ACTIVE"
    rule["next_run"] = int(time.time()) + MONTH
    redis_client.hset(key, bill, json.dumps(rule))
    return True


def stop_recurring(user_id: str, bill: str) -> bool:
    key = f"user:{user_id}:recurring"
    return redis_client.hdel(key, bill) == 1
