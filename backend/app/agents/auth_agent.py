from jose import jwt, JWTError
from fastapi import HTTPException, status
from app.config import settings

def resolve_user_id(authorization_header: str) -> int:
    if not authorization_header:
        raise HTTPException(status_code=401, detail="Missing token")

    if not authorization_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")

    token = authorization_header.split(" ")[1]

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=["HS256"],
        )
        return int(payload["sub"])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
