from sqlalchemy.orm import Session
from datetime import datetime
from rapidfuzz import fuzz

from app.db import SessionLocal
from app.models import Bill, Account, Transaction, AuditLog
from app.agents.errors import InsufficientBalanceError, InvalidRequestError


def get_unpaid_bills(user_id: str):
    """Get all unpaid bills for a user. Seeds default bills for new users."""
    db: Session = SessionLocal()
    try:
        bills = db.query(Bill).filter(
            Bill.user_id == user_id,
        ).all()
        
        # If user has NO bills at all (new user), seed some default ones for demo
        if not bills:
            default_bills = [
                Bill(user_id=user_id, name="Electricity", amount=1200, status="UNPAID"),
                Bill(user_id=user_id, name="Internet", amount=899, status="UNPAID"),
                Bill(user_id=user_id, name="Water", amount=450, status="UNPAID"),
            ]
            db.add_all(default_bills)
            db.commit()
            return default_bills
            
        return [b for b in bills if b.status == "UNPAID"]
    finally:
        db.close()


def pay_bill_by_id(user_id: str, bill_id: int):
    """
    Pay a bill by ID.
    Checks balance, updates bill status, creates transaction record.
    Returns payment details including new balance.
    """
    db: Session = SessionLocal()
    try:
        bill = db.query(Bill).filter(
            Bill.id == bill_id,
            Bill.user_id == user_id
        ).first()

        if not bill:
            raise InvalidRequestError("Bill not found")

        if bill.status == "PAID":
            raise InvalidRequestError("Bill already paid")

        account = db.query(Account).filter(
            Account.user_id == user_id
        ).first()

        if not account:
            raise InvalidRequestError("Account not found")

        if account.balance < bill.amount:
            raise InsufficientBalanceError(f"Insufficient balance. Available: ₹{account.balance}, Required: ₹{bill.amount}")

        # --- APPLY PAYMENT ---
        account.balance -= bill.amount
        new_balance = account.balance
        bill.status = "PAID"

        # Create transaction record
        txn = Transaction(
            user_id=user_id,
            bill_name=bill.name,  # Store bill name for history
            amount=bill.amount,
            status="SUCCESS",
            created_at=datetime.utcnow()
        )

        # Create audit log
        audit = AuditLog(
            user_id=user_id,
            action="PAY_BILL",
            status="SUCCESS",
            message=f"Paid {bill.name} bill for ₹{bill.amount}"
        )

        db.add(txn)
        db.add(audit)
        db.commit()

        return {
            "bill_id": bill.id,
            "bill_name": bill.name,
            "amount": bill.amount,
            "status": "PAID",
            "new_balance": new_balance
        }

    except (InsufficientBalanceError, InvalidRequestError):
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise Exception(f"Payment failed: {str(e)}")
    finally:
        db.close()


def get_account_balance(user_id: str) -> dict:
    """Get account balance for a user. Creates a default account if not found."""
    db: Session = SessionLocal()
    try:
        account = db.query(Account).filter(
            Account.user_id == user_id
        ).first()

        if not account:
            # Create a default account for new Clerk users
            account = Account(
                user_id=user_id,
                balance=10000,
                type="Savings"
            )
            db.add(account)
            db.commit()
            db.refresh(account)
            print(f"Created default account for user: {user_id}")

        return {
            "balance": account.balance,
            "account_type": account.type,
            "account_id": account.id
        }
    finally:
        db.close()


def get_transaction_history(user_id: str, limit: int = 10) -> list:
    """Get transaction history for a user"""
    db: Session = SessionLocal()
    try:
        transactions = db.query(Transaction).filter(
            Transaction.user_id == user_id
        ).order_by(Transaction.created_at.desc()).limit(limit).all()

        return transactions
    finally:
        db.close()


def find_bill_by_name(user_id: str, bill_name: str):
    """
    Find a bill by name using fuzzy matching.
    Returns the best matching unpaid bill or None.
    """
    db: Session = SessionLocal()
    try:
        bills = db.query(Bill).filter(
            Bill.user_id == user_id,
            Bill.status == "UNPAID"
        ).all()

        if not bills:
            return None

        bill_name_lower = bill_name.lower()

        # Try exact match first
        for bill in bills:
            if bill.name.lower() == bill_name_lower:
                return bill

        # Try fuzzy matching
        best_match = None
        best_score = 0

        for bill in bills:
            score = fuzz.ratio(bill_name_lower, bill.name.lower())
            if score > best_score:
                best_score = score
                best_match = bill

        # Return if score is above threshold (70%)
        if best_score >= 70:
            return best_match

        return None

    finally:
        db.close()


def find_paid_bill_by_name(user_id: str, bill_name: str):
    """
    Find a PAID bill by name using fuzzy matching.
    Used to detect 'already paid' scenarios.
    Returns the best matching paid bill or None.
    """
    db: Session = SessionLocal()
    try:
        bills = db.query(Bill).filter(
            Bill.user_id == user_id,
            Bill.status == "PAID"
        ).all()

        if not bills:
            return None

        bill_name_lower = bill_name.lower()

        # Exact match first
        for bill in bills:
            if bill.name.lower() == bill_name_lower:
                return bill

        # Fuzzy match
        best_match = None
        best_score = 0
        for bill in bills:
            score = fuzz.ratio(bill_name_lower, bill.name.lower())
            if score > best_score:
                best_score = score
                best_match = bill

        return best_match if best_score >= 70 else None

    finally:
        db.close()


def find_any_bill_by_name(user_id: str, bill_name: str):
    """
    Find ANY bill (paid or unpaid) by name using fuzzy matching.
    Returns the best matching bill or None.
    """
    db: Session = SessionLocal()
    try:
        bills = db.query(Bill).filter(
            Bill.user_id == user_id
        ).all()

        if not bills:
            return None

        bill_name_lower = bill_name.lower()

        # Try exact match first
        for bill in bills:
            if bill.name.lower() == bill_name_lower:
                return bill

        # Try fuzzy matching
        best_match = None
        best_score = 0

        for bill in bills:
            score = fuzz.ratio(bill_name_lower, bill.name.lower())
            if score > best_score:
                best_score = score
                best_match = bill

        # Return if score is above threshold (70%)
        if best_score >= 70:
            return best_match

        return None

    finally:
        db.close()

def pay_bill_by_name(user_id: str, bill_name: str):
    """Utility function for worker to pay by name"""
    bill = find_bill_by_name(user_id, bill_name)
    if not bill:
        return None
    return pay_bill_by_id(user_id, bill.id)
