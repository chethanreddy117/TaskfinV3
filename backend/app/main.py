from fastapi import FastAPI, Header, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError
from contextlib import asynccontextmanager
import time

from app.models import User, Account, Bill, Transaction



import warnings

warnings.filterwarnings("error")

from app.config import settings
from app.db import SessionLocal
from app.security import verify_password, create_access_token
from app.seed import seed_db

from app.agents.auth_agent import resolve_user_id

from app.security import hash_password
from sqlalchemy.exc import IntegrityError

from pydantic import BaseModel, Field
from app.agents.orchestrator import orchestrate

class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6) 


@asynccontextmanager
async def lifespan(app: FastAPI):
    retries = 5
    while retries:
        try:
            # Wrap seed in try/except so app doesn't crash on boot if DB is slow/down
            try:
                seed_db()
                print("Database ready")
                break
            except Exception as e:
                print(f"Seed warning (continuing anyway): {e}")
                # Don't break, allow retry logic to work, or just continue?
                # For Vercel, we often want to just fail the seed but let the App start.
                break 
        except OperationalError:
            retries -= 1
            print("Waiting for database...")
            time.sleep(2)
        except Exception as e:
            print(f"Lifespan error (ignored): {e}")
            break

    yield  # ---- application runs here ----

# APP
app = FastAPI(title="TaskFin Backend", lifespan=lifespan)

api_v1 = APIRouter(prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "TaskFin Backend is running", "docs": "/docs"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin).strip() for origin in settings.BACKEND_CORS_ORIGINS.split(",")],
    allow_origin_regex=r"https://.*\.(vercel\.app|ngrok-free\.app)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AUTH API
class LoginRequest(BaseModel):
    username: str
    password: str

@app.get("/bills")
def list_bills(user_id: int):
    return get_unpaid_bills(user_id)


@app.post("/bills/pay")
def pay_bill_api(user_id: int, bill_id: int):
    return pay_bill(bill_id, user_id)



@api_v1.post("/auth/login")
def login(req: LoginRequest):
    db = SessionLocal()
    user = db.query(User).filter(User.username == req.username).first()
    db.close()

    if not user or not verify_password(req.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token}

#Register

@api_v1.post("/auth/register")
def register(req: RegisterRequest):
    db = SessionLocal()

    try:
        # check if user already exists
        if db.query(User).filter(User.username == req.username).first():
            raise HTTPException(
                status_code=400,
                detail="Username already exists"
            )

        user = User(
            username=req.username,
            password=hash_password(req.password),
        )

        db.add(user)
        db.commit()

        return {"message": "User registered successfully"}

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Registration failed"
        )
    finally:
        db.close()


# HEALTH

@api_v1.get("/health")
def health():
    return {"status": "healthy"}

# CHAT API 

class ChatRequest(BaseModel):
    message: str

@api_v1.post("/agent/chat")
async def agent_chat(
    req: ChatRequest,
    authorization: str = Header(...)
):
    from app.agents.orchestrator import orchestrate   # import here to avoid circular issues

    user_id = resolve_user_id(authorization)
    result = await orchestrate(user_id, req.message)
    return {"response": result.message}
# ME
@api_v1.get("/me")
def me(authorization: str = Header(...)):
    user_id = resolve_user_id(authorization)
    return {"user_id": user_id}

app.include_router(api_v1)
