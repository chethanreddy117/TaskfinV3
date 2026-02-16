# app/seed.py
from app.db import SessionLocal, engine, Base
from app.models import User, Bill, Account
from app.security import hash_password

from app.services.redis_client import redis_client

def seed_db():
    """
    Seed the database with demo data for TaskFin.
    Creates a demo user 'chethan' with various bills for testing.
    """
    from app.config import settings
    
    # Log database URL (obfuscated) for debugging
    db_url_display = settings.DATABASE_URL if settings.DATABASE_URL else "NOT SET"
    if db_url_display != "NOT SET" and "@" in db_url_display:
        parts = db_url_display.split("@")
        credentials = parts[0].split("://")[1]
        if ":" in credentials:
            user = credentials.split(":")[0]
            db_url_display = db_url_display.replace(credentials, f"{user}:****")
    
    print(f"🔗 Database URL: {db_url_display}")
    
    # -------------------------------
    # Create tables (demo-safe)
    # -------------------------------
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created")
    except Exception as e:
        print(f"❌ Failed to create tables: {str(e)}")
        raise

    db = SessionLocal()

    try:
        # -------------------------------
        # USER
        # -------------------------------
        user = db.query(User).filter_by(username="chethan").first()
        if not user:
            user = User(
                username="chethan",
                password=hash_password("1234"),
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"✓ Created demo user: chethan")
        else:
            print(f"✓ Demo user already exists: chethan")

        user_id = user.id

        # -------------------------------
        # ACCOUNT
        # -------------------------------
        account = db.query(Account).filter_by(user_id=user_id).first()
        if not account:
            account = Account(
                user_id=user_id,
                balance=15000,  # Higher balance for testing multiple payments
                type="Savings",
            )
            db.add(account)
            db.commit()
            print(f"✓ Created account with balance: ₹15,000")
        else:
            print(f"✓ Account already exists with balance: ₹{account.balance}")

        # -------------------------------
        # BILLS - More diverse bills for better demo
        # -------------------------------
        existing_bills = db.query(Bill).filter_by(user_id=user_id, status="UNPAID").count()
        if existing_bills == 0:
            bills = [
                Bill(
                    user_id=user_id,
                    name="Electricity",
                    amount=1200,
                    status="UNPAID",
                ),
                Bill(
                    user_id=user_id,
                    name="Water",
                    amount=450,
                    status="UNPAID",
                ),
                Bill(
                    user_id=user_id,
                    name="Internet",
                    amount=899,
                    status="UNPAID",
                ),
                Bill(
                    user_id=user_id,
                    name="Mobile",
                    amount=599,
                    status="UNPAID",
                ),
                Bill(
                    user_id=user_id,
                    name="Gas",
                    amount=850,
                    status="UNPAID",
                ),
            ]
            db.add_all(bills)
            db.commit()
            print(f"✓ Created {len(bills)} demo bills")
        else:
            print(f"✓ Bills already exist: {existing_bills} unpaid bills")

        # -------------------------------
        # REDIS - Clear risk counters for fresh demo
        # -------------------------------
        try:
            from datetime import date
            today = date.today().isoformat()
            redis_client.delete(f"risk:amount:{user_id}:{today}")
            redis_client.delete(f"risk:count:{user_id}:{today}")
            print(f"✓ Reset risk counters for today")
        except Exception as e:
            print(f"⚠️ Redis unavailable (skipping risk counter reset): {e}")

        print("\n🎉 Seed completed successfully!")
        print(f"   Demo Login: username='chethan', password='1234'")
        print(f"   Initial Balance: ₹{account.balance}")
        print(f"   Unpaid Bills: {existing_bills if existing_bills > 0 else len(bills)}")

    except Exception as e:
        print(f"❌ Seed failed: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()
