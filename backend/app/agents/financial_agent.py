from app.services.billing_service import get_unpaid_bills, pay_bill_by_id, get_account_balance, get_transaction_history, find_bill_by_name, find_paid_bill_by_name
from app.services.state_service import get_state, set_state, clear_state
from app.agents.types import AgentResult
from app.agents.errors import InvalidRequestError, InsufficientBalanceError
from app.agents.audit_agent import AuditAgent
from app.db import SessionLocal
from app.models import Account, Transaction
from rapidfuzz import fuzz
import re


class FinancialAgent:
    """
    Financial Agent handles all money-related operations:
    - Listing unpaid bills
    - Processing bill payments with confirmation
    - Checking account balance
    - Viewing transaction history
    """

    def __init__(self):
        self.audit_agent = AuditAgent()

    async def handle(self, user_id: int, message: str) -> AgentResult:
        """
        Main handler for payment flow with confirmation logic.
        Handles both initial payment request and confirmation response.
        """
        state = get_state(user_id)

        # STEP 1: Handle confirmation/cancellation if awaiting one
        if state.get("awaiting_confirmation"):
            message_lower = message.lower().strip()
            
            # User is canceling
            if message_lower in ["no", "cancel", "nevermind", "nope", "nah", "stop"]:
                bill_id = state.get("bill_id")
                clear_state(user_id)
                
                # Log cancellation
                self.audit_agent.log_event(
                    user_id=user_id,
                    action="PAYMENT_CANCELLED",
                    status="SUCCESS",
                    message=f"User cancelled payment for bill_id={bill_id}"
                )
                
                return AgentResult(
                    success=True,
                    message="Payment cancelled. Is there anything else I can help you with?",
                    data=None
                )
            
            # User is confirming
            if message_lower in ["yes", "confirm", "proceed", "ok", "yeah", "yep", "sure", "pay"]:
                bill_id = state["bill_id"]
                bill_name = state.get("bill_name", "bill")
                
                try:
                    # Check risk limits before payment
                    from app.agents.risk_agent import RiskAgent
                    risk_agent = RiskAgent()
                    
                    # Get bill amount for risk check
                    bills = get_unpaid_bills(user_id)
                    bill = next((b for b in bills if b.id == bill_id), None)
                    
                    if not bill:
                        clear_state(user_id)
                        return AgentResult(
                            success=False,
                            message="Bill not found. It may have been already paid.",
                            data=None
                        )
                    
                    # Evaluate risk
                    risk_result = await risk_agent.evaluate_payment_risk(user_id, bill.amount)
                    
                    if not risk_result["approved"]:
                        clear_state(user_id)
                        
                        # Log risk block
                        self.audit_agent.log_event(
                            user_id=user_id,
                            action="PAYMENT_BLOCKED_RISK",
                            status="BLOCKED",
                            message=f"Payment blocked: {risk_result['reason']}"
                        )
                        
                        return AgentResult(
                            success=False,
                            message=f"Payment blocked: {risk_result['reason']}",
                            data=risk_result
                        )
                    
                    # Attempt payment
                    result = pay_bill_by_id(user_id, bill_id)
                    clear_state(user_id)
                    
                    # Update risk counters
                    await risk_agent.record_payment(user_id, bill.amount)
                    
                    # Log successful payment
                    self.audit_agent.log_event(
                        user_id=user_id,
                        action="PAYMENT_EXECUTED",
                        status="SUCCESS",
                        message=f"Paid {bill_name} bill for ₹{result['amount']}"
                    )
                    
                    return AgentResult(
                        success=True,
                        message=f"✓ Payment successful!\n\n{bill_name} bill of ₹{result['amount']} has been paid.\n\nYour updated balance: ₹{result.get('new_balance', 'N/A')}",
                        data=result
                    )
                    
                except InsufficientBalanceError as e:
                    clear_state(user_id)
                    
                    # Log insufficient balance
                    self.audit_agent.log_event(
                        user_id=user_id,
                        action="PAYMENT_BLOCKED_INSUFFICIENT_FUNDS",
                        status="BLOCKED",
                        message=str(e)
                    )
                    
                    return AgentResult(
                        success=False,
                        message=f"Payment failed: Insufficient balance. Please check your account balance.",
                        data=None
                    )
                    
                except Exception as e:
                    clear_state(user_id)
                    
                    # Log payment failure
                    self.audit_agent.log_event(
                        user_id=user_id,
                        action="PAYMENT_FAILED",
                        status="FAILED",
                        message=str(e)
                    )
                    
                    return AgentResult(
                        success=False,
                        message=f"Payment failed: {str(e)}",
                        data=None
                    )

        # STEP 2: Initial payment intent - find which bill to pay
        bills = get_unpaid_bills(user_id)

        if not bills:
            return AgentResult(
                success=True,
                message="You have no unpaid bills. All caught up! 🎉",
                data=None
            )

        # Check for "pay all" or "pay everything" intent
        if re.search(r"\b(all|everything)\b", message.lower()):
            bill_list = "\n".join([f"• {b.name}: ₹{b.amount}" for b in bills])
            return AgentResult(
                success=False,
                message=f"I can process one bill at a time. Which one would you like to start with?\n\n{bill_list}",
                data=None
            )

        # Try to extract bill keyword from message
        bill_keyword = self._extract_bill_keyword(message)
        
        if bill_keyword:
            # User specified a bill name, try to match unpaid first
            matched_bill = find_bill_by_name(user_id, bill_keyword)

            if matched_bill:
                bill = matched_bill
            else:
                # Not in unpaid list — check if it was already paid
                paid_bill = find_paid_bill_by_name(user_id, bill_keyword)
                if paid_bill:
                    paid_on = paid_bill.updated_at.strftime("%d %b %Y") if getattr(paid_bill, "updated_at", None) else "recently"
                    return AgentResult(
                        success=False,
                        message=(
                            f"✅ Payment already done!\n\n"
                            f"Your **{paid_bill.name}** bill of ₹{paid_bill.amount} "
                            f"was paid on {paid_on}.\n\n"
                            f"Would you like to pay a different bill?"
                        ),
                        data={"bill_name": paid_bill.name, "amount": paid_bill.amount, "status": "PAID"}
                    )

                # Not found anywhere — show unpaid list
                bill_list = "\n".join([f"• {b.name} - ₹{b.amount}" for b in bills])
                return AgentResult(
                    success=False,
                    message=f"I couldn't find a bill matching '{bill_keyword}'.\n\nYour unpaid bills:\n{bill_list}\n\nPlease specify which bill you'd like to pay.",
                    data=None
                )
        else:
            # No bill name specified
            # SAFETY CHECK: Only default if there's exactly one unpaid bill
            if len(bills) == 1:
                self._log(f"No keyword found. Defaulting to single unpaid bill: {bills[0].name}")
                bill = bills[0]
            else:
                self._log("No keyword found and multiple bills exist. Asking for clarification.")
                bill_list = "\n".join([f"• {b.name}: ₹{b.amount}" for b in bills])
                return AgentResult(
                    success=False,
                    message=f"I found multiple unpaid bills. Which one would you like to pay?\n\n{bill_list}",
                    data=None
                )

        # Set confirmation state
        set_state(user_id, {
            "current_task": "PAY_BILL",
            "bill_id": bill.id,
            "bill_name": bill.name,
            "awaiting_confirmation": True
        }, ttl=60)  # 60 second confirmation timeout

        # Log payment request
        self.audit_agent.log_event(
            user_id=user_id,
            action="PAYMENT_REQUESTED",
            status="PENDING",
            message=f"User requested to pay {bill.name} bill of ₹{bill.amount}"
        )

        return AgentResult(
            success=False,
            message=f"💳 Payment Confirmation\n\n{bill.name}: ₹{bill.amount}\n\nConfirm payment? (yes/no)",
            data={"bill_id": bill.id, "bill_name": bill.name, "amount": bill.amount}
        )

    async def handle_list_bills(self, user_id: int) -> AgentResult:
        """List all unpaid bills for the user"""
        bills = get_unpaid_bills(user_id)
        
        # Log bill view
        self.audit_agent.log_event(
            user_id=user_id,
            action="BILLS_VIEWED",
            status="SUCCESS",
            message=f"User viewed {len(bills)} unpaid bills"
        )

        if not bills:
            return AgentResult(
                success=True,
                message="You have no unpaid bills. All caught up! 🎉",
                data=[]
            )

        # Format bills nicely
        bill_list = []
        total = 0
        for bill in bills:
            bill_list.append(f"• {bill.name}: ₹{bill.amount}")
            total += bill.amount

        message = f"📋 Your Unpaid Bills:\n\n" + "\n".join(bill_list) + f"\n\nTotal: ₹{total}"

        return AgentResult(
            success=True,
            message=message,
            data=[{"id": b.id, "name": b.name, "amount": b.amount} for b in bills]
        )

    async def handle_balance(self, user_id: int) -> AgentResult:
        """Check account balance"""
        balance_info = get_account_balance(user_id)
        
        # Log balance check
        self.audit_agent.log_event(
            user_id=user_id,
            action="BALANCE_VIEWED",
            status="SUCCESS",
            message=f"User checked balance: ₹{balance_info['balance']}"
        )

        return AgentResult(
            success=True,
            message=f"💰 Account Balance\n\nCurrent Balance: ₹{balance_info['balance']}\nAccount Type: {balance_info['account_type']}",
            data=balance_info
        )

    async def handle_history(self, user_id: int, limit: int = 10) -> AgentResult:
        """Show transaction history"""
        transactions = get_transaction_history(user_id, limit)
        
        # Log history view
        self.audit_agent.log_event(
            user_id=user_id,
            action="HISTORY_VIEWED",
            status="SUCCESS",
            message=f"User viewed transaction history ({len(transactions)} transactions)"
        )

        if not transactions:
            return AgentResult(
                success=True,
                message="No transaction history found. Make your first payment to see it here!",
                data=[]
            )

        # Format transactions
        txn_list = []
        for txn in transactions:
            date_str = txn.created_at.strftime("%Y-%m-%d %H:%M") if txn.created_at else "N/A"
            status_emoji = "✓" if txn.status == "SUCCESS" else "✗"
            txn_list.append(f"{status_emoji} {date_str} | {txn.bill_name} | ₹{txn.amount}")

        message = f"📜 Recent Transactions:\n\n" + "\n".join(txn_list)

        return AgentResult(
            success=True,
            message=message,
            data=[{
                "bill_name": t.bill_name,
                "amount": t.amount,
                "status": t.status,
                "date": t.created_at.isoformat() if t.created_at else None
            } for t in transactions]
        )

    def _extract_bill_keyword(self, message: str) -> str | None:
        """
        Extract the bill-type keyword from a user payment message.
        Strips common filler words and returns the remaining keyword,
        which is then used for DB-level fuzzy matching (paid + unpaid).
        """
        message_lower = message.lower()

        self._log(f"Extracting keyword from: {message_lower}")
        # Strip common payment/filler words
        pattern = r"\b(" + "|".join([
            "pay", "payment", "bill", "bills", "the", "my",
            "make", "a", "an", "please", "settle", "clear"
        ]) + r")\b"
        keyword = re.sub(pattern, "", message_lower).strip()
        self._log(f"Extracted keyword: '{keyword}'")

        return keyword if keyword else None

    def _log(self, msg):
        try:
            with open("app/debug.log", "a") as f:
                f.write(msg + "\n")
        except:
            pass
