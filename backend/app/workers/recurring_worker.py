import time
import json
from datetime import datetime

from app.services.recurring_service import get_all_recurring
from app.services.billing_service import pay_bill_by_name
from app.services.billing_service import adjust_balance, record_transaction

CHECK_INTERVAL = 10  # seconds


def run_recurring_worker():
    print("Recurring worker started")

    while True:
        now = int(time.time())
        all_rules = get_all_recurring()  # all users

        for user_id, rules in all_rules.items():
            for rule in rules:
                if rule["status"] != "ACTIVE":
                    continue

                if rule["next_run"] <= now:
                    bill = rule["bill"]
                    amount = rule["amount"]

                    success = pay_bill_by_name(user_id, bill)
                    if success:
                        adjust_balance(user_id, -amount)
                        record_transaction(user_id, {
                            "type": "RECURRING_PAYMENT",
                            "bill": bill,
                            "amount": amount,
                            "status": "SUCCESS",
                            "ts": now,
                        })

                        # schedule next month
                        rule["next_run"] = now + (30 * 24 * 60 * 60)
                        rule["last_run"] = now
                        rule["last_status"] = "SUCCESS"

                        # save updated rule
                        from app.services.recurring_service import update_recurring
                        update_recurring(user_id, rule)

        time.sleep(CHECK_INTERVAL)
