from rapidfuzz import fuzz

bills = ["Electricity", "Internet", "Mobile", "Gas"]
inputs = [
    "pay my water bill",
    "pay all bills"
]

print("--- Fuzzy Match Debug ---")
for msg in inputs:
    print(f"\nInput: '{msg}'")
    best_score = 0
    best_match = None
    
    for bill in bills:
        score = fuzz.partial_ratio(msg.lower(), bill.lower())
        print(f"  vs '{bill}': {score}")
        if score > best_score:
            best_score = score
            best_match = bill
            
    print(f"Best Match: {best_match} (Score: {best_score})")
