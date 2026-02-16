from app.services.redis_client import redis_client

def get_balance(user_id: int) -> int:
    key = f"user:{user_id}:balance"
    value = redis_client.get(key)
    return int(value) if value else 0


def set_balance(user_id: int, amount: int):
    redis_client.set(f"user:{user_id}:balance", amount)


def adjust_balance(user_id: int, delta: int):
    redis_client.incrby(f"user:{user_id}:balance", delta)

# def record_transaction(user_id: int, txn: dict):
#     redis_client.rpush(
#         f"user:{user_id}:transactions",
#         json.dumps(txn)
#     )


# def get_transactions(user_id: int, limit=10):
#     raw = redis_client.lrange(f"user:{user_id}:transactions", -limit, -1)
#     return [json.loads(x) for x in raw]
