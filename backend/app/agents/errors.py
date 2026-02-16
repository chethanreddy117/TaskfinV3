from enum import Enum, auto

class ErrorType(Enum):
    INVALID_INPUT = auto()
    NOT_FOUND = auto()
    INSUFFICIENT_FUNDS = auto()
    CONFLICT = auto()
    TIMEOUT = auto()   
    INTERNAL_ERROR = auto()
    UNKNOWN_INTENT = auto()

class InsufficientBalanceError(Exception):
    pass

class UnauthorizedError(Exception):
    pass

class InvalidRequestError(Exception):
    pass
