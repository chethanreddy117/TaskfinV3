from typing import List, Dict

# Mock data (fast, demo-safe)
BILLS = [
    {"id": 1, "name": "Credit Card", "amount": 2500, "status": "unpaid"},
    {"id": 2, "name": "Electricity", "amount": 1200, "status": "unpaid"},
]

def list_bills() -> List[Dict]:
    return BILLS

def pay_bill(bill_id: int) -> Dict:
    for bill in BILLS:
        if bill["id"] == bill_id:
            if bill["status"] == "paid":
                return {"message": "Bill already paid"}
            bill["status"] = "paid"
            return {"message": f"{bill['name']} bill paid successfully"}
    return {"message": "Bill not found"}
