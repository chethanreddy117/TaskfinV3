import requests
from jose import jwt, JWTError
from fastapi import HTTPException, status
from app.config import settings

from app.db import SessionLocal
from app.models import User

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

def resolve_user_id(authorization_header: str) -> str:
    """
    Verifies the Clerk session token and returns the Clerk User ID (sub).
    Ensures a User record exists in the local database.
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
        
        clerk_user_id = payload.get("sub")
        if not clerk_user_id:
            raise HTTPException(status_code=401, detail="Token missing subject (sub)")

        # Ensure user exists in local database
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == clerk_user_id).first()
            if not user:
                # If you want to fetch more details from Clerk, you'd call Clerk Backend API here.
                # For now, we'll just create a placeholder user so foreign keys work.
                # We can use the user's ID as a temporary username or just 'clerk_user'
                user = User(
                    id=clerk_user_id,
                    username=f"user_{clerk_user_id[-6:]}", # Last 6 chars of ID as temporary username
                    password=None # Clerk users don't have local passwords
                )
                db.add(user)
                db.commit()
                print(f"Automatically created local User record for Clerk ID: {clerk_user_id}")
            
            return clerk_user_id
        finally:
            db.close()

    except JWTError as e:
        print(f"JWT Verification Error: {e}")
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {str(e)}")
    except Exception as e:
        print(f"Unexpected Auth Error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")
