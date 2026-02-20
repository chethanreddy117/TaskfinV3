import requests
from jose import jwt, JWTError
from fastapi import HTTPException, status
from app.config import settings

# Cache for JWKS
_jwks_cache = None

def get_jwks():
    global _jwks_cache
    if _jwks_cache is None:
        try:
            # Derived from the publishable key domain or hardcoded for this instance
            # Domain: ruling-lark-21.clerk.accounts.dev
            jwks_url = "https://ruling-lark-21.clerk.accounts.dev/.well-known/jwks.json"
            response = requests.get(jwks_url)
            response.raise_for_status()
            _jwks_cache = response.json()
        except Exception as e:
            print(f"Error fetching JWKS: {e}")
            return None
    return _jwks_cache

def resolve_user_id(authorization_header: str) -> int:
    """
    Verifies the Clerk session token and returns dummy user ID 1.
    """
    if not authorization_header:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    if not authorization_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")

    token = authorization_header.split(" ")[1]

    jwks = get_jwks()
    if not jwks:
        raise HTTPException(status_code=500, detail="Could not verify token (JWKS unavailable)")

    try:
        # Get the 'kid' from the token header to find the matching public key
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        if not kid:
            raise HTTPException(status_code=401, detail="Missing 'kid' in token header")

        # Find the correct key in the JWKS
        key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
        if not key:
            raise HTTPException(status_code=401, detail="Key not found in JWKS")

        # Verify the token using the found public key
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            options={"verify_aud": False}
        )
        
        # For now, return the dummy ID 1 as requested
        return 1

    except JWTError as e:
        print(f"JWT Verification Error: {e}")
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {str(e)}")
    except Exception as e:
        print(f"Unexpected Auth Error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")
