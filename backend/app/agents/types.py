from dataclasses import dataclass
from typing import Optional, Dict, Any
from app.agents.errors import ErrorType


@dataclass
class AgentResult:
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error_type: Optional[ErrorType] = None
