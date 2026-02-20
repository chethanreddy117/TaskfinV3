import time
import json
from datetime import datetime

from app.services.recurring_service import get_all_recurring
from app.services.billing_service import pay_bill_by_name

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
                    bill_name = rule["bill"]
                    
                    # pay_bill_by_name handles balance reduction and transaction recording
                    result = pay_bill_by_name(user_id, bill_name)
                    if result:
                        print(f"✓ Recurring payment successful for {user_id}: {bill_name}")
                        # schedule next month
                        rule["next_run"] = now + (30 * 24 * 60 * 60)
                        rule["last_run"] = now
                        rule["last_status"] = "SUCCESS"

                        # save updated rule
                        from app.services.recurring_service import update_recurring
                        update_recurring(user_id, rule)
                    else:
                        print(f"✗ Recurring payment failed for {user_id}: {bill_name}")

        time.sleep(CHECK_INTERVAL)
