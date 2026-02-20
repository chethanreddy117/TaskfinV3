from datetime import date, datetime
from app.services.redis_client import redis_client
from app.agents.types import AgentResult
from app.agents.audit_agent import AuditAgent

# ---- Policy constants (easy to tune) ----
DAILY_AMOUNT_LIMIT = 5000  # INR
MAX_PAYMENTS_PER_DAY = 5


class RiskAgent:
    """
    Risk Agent enforces safety controls:
    - Daily amount spending limit (₹5000)
    - Daily payment count limit (5 payments)
    - Risk status reporting
    """

    def __init__(self):
        self.audit_agent = AuditAgent()

    async def evaluate_payment_risk(self, user_id: str, amount: int) -> dict:
        """
        Evaluate if a payment is within risk limits.
        Returns dict with 'approved' (bool) and 'reason' (str)
        """
        today = date.today().isoformat()

        # ---- Check daily amount limit ----
        amount_key = f"risk:amount:{user_id}:{today}"
        current_amount = redis_client.get(amount_key)
        current_amount = int(current_amount) if current_amount else 0

        if current_amount + amount > DAILY_AMOUNT_LIMIT:
            return {
                "approved": False,
                "reason": f"Daily spending limit exceeded. You've spent ₹{current_amount} today (limit: ₹{DAILY_AMOUNT_LIMIT})",
                "current_amount": current_amount,
                "limit": DAILY_AMOUNT_LIMIT
            }

        # ---- Check payment count limit ----
        count_key = f"risk:count:{user_id}:{today}"
        count = redis_client.get(count_key)
        count = int(count) if count else 0

        if count >= MAX_PAYMENTS_PER_DAY:
            return {
                "approved": False,
                "reason": f"Daily payment limit reached. You've made {count} payments today (limit: {MAX_PAYMENTS_PER_DAY})",
                "current_count": count,
                "limit": MAX_PAYMENTS_PER_DAY
            }

        return {
            "approved": True,
            "reason": "Payment approved",
            "current_amount": current_amount,
            "current_count": count
        }

    async def record_payment(self, user_id: str, amount: int) -> None:
        """
        Record a successful payment in risk tracking.
        Updates both amount and count for the day.
        """
        today = date.today().isoformat()

        # Increment amount
        amount_key = f"risk:amount:{user_id}:{today}"
        redis_client.incrby(amount_key, amount)
        redis_client.expire(amount_key, 86400)  # Expire at end of day

        # Increment count
        count_key = f"risk:count:{user_id}:{today}"
        redis_client.incr(count_key)
        redis_client.expire(count_key, 86400)  # Expire at end of day

    async def handle_risk_status(self, user_id: str) -> AgentResult:
        """
        Handle user request to check their risk/spending status.
        Shows current usage vs limits.
        """
        today = date.today().isoformat()

        # Get current usage
        amount_key = f"risk:amount:{user_id}:{today}"
        current_amount = redis_client.get(amount_key)
        current_amount = int(current_amount) if current_amount else 0

        count_key = f"risk:count:{user_id}:{today}"
        count = redis_client.get(count_key)
        count = int(count) if count else 0

        # Calculate remaining
        remaining_amount = DAILY_AMOUNT_LIMIT - current_amount
        remaining_payments = MAX_PAYMENTS_PER_DAY - count

        message = f"""📊 Daily Spending Limits

Amount:
• Used: ₹{current_amount}
• Limit: ₹{DAILY_AMOUNT_LIMIT}
• Remaining: ₹{remaining_amount}

Payments:
• Made: {count}
• Limit: {MAX_PAYMENTS_PER_DAY}
• Remaining: {remaining_payments}"""

        return AgentResult(
            success=True,
            message=message,
            data={
                "amount_used": current_amount,
                "amount_limit": DAILY_AMOUNT_LIMIT,
                "amount_remaining": remaining_amount,
                "count_used": count,
                "count_limit": MAX_PAYMENTS_PER_DAY,
                "count_remaining": remaining_payments
            }
        )


# Legacy function for backward compatibility
def assess_payment_risk(
    user_id: str,
    bill_name: str,
    amount: int
) -> tuple[bool, str]:
    """
    Legacy function - use RiskAgent.evaluate_payment_risk instead.
    Returns: (True, "approved") OR (False, reason)
    """
    today = date.today().isoformat()

    # ---- Daily amount limit ----
    amount_key = f"risk:amount:{user_id}:{today}"
    current_amount = redis_client.get(amount_key)
    current_amount = int(current_amount) if current_amount else 0

    if current_amount + amount > DAILY_AMOUNT_LIMIT:
        return False, "Daily payment limit exceeded."

    # ---- Payment count limit ----
    count_key = f"risk:count:{user_id}:{today}"
    count = redis_client.get(count_key)
    count = int(count) if count else 0

    if count >= MAX_PAYMENTS_PER_DAY:
        return False, "Too many payments today."

    return True, "approved"
