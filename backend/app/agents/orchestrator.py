from app.agents.financial_agent import FinancialAgent
from app.agents.audit_agent import AuditAgent
from app.agents.risk_agent import RiskAgent
from app.agents.types import AgentResult
from app.agents.base import llm
from app.services.state_service import get_state
import re



# Enhanced intent detection prompt
INTENT_PROMPT = """
You are an intent classifier for a financial bill payment assistant.

Classify the user message into ONE of these categories:
- GREETING: User is saying hello, hi, hey, or general greeting
- LIST_BILLS: User wants to see unpaid bills (e.g., "show bills", "list bills", "what bills do I have")
- PAY_BILL: User wants to pay a bill (e.g., "pay electricity", "pay bill", "make payment")
- SHOW_BALANCE: User wants to check account balance (e.g., "check balance", "show balance", "account balance")
- SHOW_HISTORY: User wants to see transaction history (e.g., "show history", "payment history", "transactions")
- CHECK_RISK: User wants to know their spending limits or risk status
- CONFIRMATION: User is confirming an action (e.g., "yes", "confirm", "proceed", "ok")
- CANCELLATION: User is canceling an action (e.g., "no", "cancel", "nevermind")
- UNKNOWN: None of the above

Return ONLY the category name.

User message: {message}
"""


class Orchestrator:
    """
    Main orchestrator agent that routes user requests to specialized agents.
    Handles intent detection, conversation state, and response coordination.
    """

    def __init__(self):
        self.financial_agent = FinancialAgent()
        self.audit_agent = AuditAgent()
        self.risk_agent = RiskAgent()

    async def route(self, user_id: int, message: str) -> AgentResult:
        """
        Route user message to appropriate agent based on intent detection.
        This is the internal routing method.
        """
        try:
            # Get conversation state
            state = get_state(user_id)
            
            # Simple pattern matching for common intents (faster than LLM)
            message_lower = message.lower().strip()
            
            # Handle greetings
            if self._is_greeting(message_lower):
                return AgentResult(
                    success=True,
                    message="Hello! I'm your TaskFin assistant. I can help you with:\n• Show unpaid bills\n• Pay bills\n• Check your account balance\n• View payment history\n\nWhat would you like to do?",
                    data=None
                )
            
            # Handle confirmations/cancellations — always check cancellation
            # even if state expired, so "no" never falls through to UNKNOWN
            if self._is_cancellation(message_lower):
                return await self.financial_agent.handle(user_id, message)

            if state.get("awaiting_confirmation"):
                if self._is_confirmation(message_lower):
                    return await self.financial_agent.handle(user_id, message)
                # Non-confirmation/cancellation while awaiting — remind user
                return AgentResult(
                    success=False,
                    message="Please reply **yes** to confirm or **no** to cancel the pending payment.",
                    data=None
                )

            # Pattern-based intent detection for speed
            if self._is_list_bills(message_lower):
                return await self.financial_agent.handle_list_bills(user_id)
            
            if self._is_pay_bill(message_lower):
                return await self.financial_agent.handle(user_id, message)
            
            if self._is_show_balance(message_lower):
                return await self.financial_agent.handle_balance(user_id)
            
            if self._is_show_history(message_lower):
                return await self.financial_agent.handle_history(user_id)
            
            if self._is_check_risk(message_lower):
                return await self.risk_agent.handle_risk_status(user_id)
            
            # Fallback to LLM intent detection for complex cases
            intent = await self._detect_intent_llm(message)
            
            if intent == "GREETING":
                return AgentResult(
                    success=True,
                    message="Hello! How can I help you today? You can ask me to show bills, make payments, check balance, or view history.",
                    data=None
                )
            
            if intent == "LIST_BILLS":
                return await self.financial_agent.handle_list_bills(user_id)
            
            if intent == "PAY_BILL":
                return await self.financial_agent.handle(user_id, message)
            
            if intent == "SHOW_BALANCE":
                return await self.financial_agent.handle_balance(user_id)
            
            if intent == "SHOW_HISTORY":
                return await self.financial_agent.handle_history(user_id)
            
            if intent == "CHECK_RISK":
                return await self.risk_agent.handle_risk_status(user_id)
            
            if intent == "CONFIRMATION":
                # "Yes" without context usually means "Yes, I want to pay/continue"
                return await self.financial_agent.handle_list_bills(user_id)

            if intent == "CANCELLATION":
                return AgentResult(
                    success=True,
                    message="Okay! Let me know if there's anything else I can help you with.",
                    data=None
                )

            # Unknown intent
            return AgentResult(
                success=False,
                message="I'm not sure what you're asking for. Try:\n• 'show my bills'\n• 'pay [bill name]'\n• 'check balance'\n• 'show history'",
                data=None
            )
            
        except Exception as e:
            print(f"Orchestrator error: {str(e)}")
            return AgentResult(
                success=False,
                message="I encountered an error processing your request. Please try again.",
                data=None
            )
    
    # Pattern matching helpers (faster than LLM)
    def _is_greeting(self, msg: str) -> bool:
        greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']
        # Check for whole word matches to avoid false positives (e.g., "hi" in "history")
        words = msg.split()
        return any(g in words or g in msg for g in greetings if ' ' in g or g in words)
    
    def _is_confirmation(self, msg: str) -> bool:
        confirmations = ['yes', 'confirm', 'proceed', 'ok', 'yeah', 'yep', 'sure', 'pay']
        return msg in confirmations
    
    def _is_cancellation(self, msg: str) -> bool:
        cancellations = ['no', 'cancel', 'nevermind', 'nope', 'nah', 'stop']
        return msg in cancellations
    
    def _is_list_bills(self, msg: str) -> bool:
        patterns = ['show bill', 'list bill', 'my bill', 'unpaid', 'what bill', 'view bill']
        return any(p in msg for p in patterns)
    
    def _is_pay_bill(self, msg: str) -> bool:
        patterns = ['pay', 'make payment', 'settle']
        return any(p in msg for p in patterns)
    
    def _is_show_balance(self, msg: str) -> bool:
        patterns = ['balance', 'how much', 'account']
        return any(p in msg for p in patterns) and 'history' not in msg
    
    def _is_show_history(self, msg: str) -> bool:
        patterns = ['history', 'transaction', 'past payment', 'previous payment']
        return any(p in msg for p in patterns)
    
    def _is_check_risk(self, msg: str) -> bool:
        patterns = ['limit', 'risk', 'how much can i', 'spending']
        return any(p in msg for p in patterns)
    
    async def _detect_intent_llm(self, message: str) -> str:
        """Fallback LLM-based intent detection for complex cases"""
        try:
            response = llm.invoke(INTENT_PROMPT.format(message=message))
            return response.content.strip().upper()
        except Exception as e:
            print(f"LLM intent detection error: {str(e)}")
            return "UNKNOWN"


# Global orchestrator instance
_orchestrator = None

async def orchestrate(user_id: int, message: str) -> AgentResult:
    """
    Main entry point for orchestrating user requests.
    This is the async function called by main.py
    """
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    
    return await _orchestrator.route(user_id, message)
