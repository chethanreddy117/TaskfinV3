#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Initialization Script for TaskFin

This script creates all database tables and seeds initial demo data.
Run this script manually to set up your Supabase database.

Usage:
    python init_db.py

Environment Variables Required:
    - POSTGRES_URL or DATABASE_URL: Supabase connection string
    - JWT_SECRET_KEY: Secret key for JWT tokens
    - ANTHROPIC_API_KEY: API key for Anthropic Claude
"""

import sys
import os

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

def main():
    print("=" * 60)
    print("TaskFin Database Initialization")
    print("=" * 60)
    print()

    # Check environment variables
    from app.config import settings
    
    if not settings.DATABASE_URL:
        print("[ERROR] DATABASE_URL not found!")
        print()
        print("Please set the POSTGRES_URL environment variable.")
        print("Get it from: Supabase Dashboard -> Project Settings -> Database")
        print()
        print("Example:")
        print("  export POSTGRES_URL='postgresql://postgres:[password]@[host]/postgres'")
        print()
        sys.exit(1)
    
    # Obfuscate password in URL for logging
    db_url_display = settings.DATABASE_URL
    if "@" in db_url_display:
        parts = db_url_display.split("@")
        credentials = parts[0].split("://")[1]
        if ":" in credentials:
            user = credentials.split(":")[0]
            db_url_display = db_url_display.replace(credentials, f"{user}:****")
    
    print(f"[DB] Database URL: {db_url_display}")
    print()

    # Import after config is loaded
    from app.db import engine, Base, SessionLocal
    from app.models import User, Account, Bill, Transaction, AuditLog
    from app.security import hash_password
    
    try:
        # Step 1: Create all tables
        print("[*] Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("[OK] Tables created successfully!")
        print()
        
        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"[INFO] Tables in database: {', '.join(tables)}")
        print()
        
        # Step 2: Seed demo data
        print("[*] Seeding demo data...")
        db = SessionLocal()
        
        try:
            # Check if demo user exists
            user = db.query(User).filter_by(username="chethan").first()
            if not user:
                user = User(
                    username="chethan",
                    password=hash_password("1234"),
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                print("[OK] Created demo user: chethan")
            else:
                print("[INFO] Demo user already exists: chethan")
            
            user_id = user.id
            
            # Create account
            account = db.query(Account).filter_by(user_id=user_id).first()
            if not account:
                account = Account(
                    user_id=user_id,
                    balance=15000,
                    type="Savings",
                )
                db.add(account)
                db.commit()
                print("[OK] Created account with balance: Rs.15,000")
            else:
                print(f"[INFO] Account already exists with balance: Rs.{account.balance}")
            
            # Create bills
            existing_bills = db.query(Bill).filter_by(user_id=user_id, status="UNPAID").count()
            if existing_bills == 0:
                bills = [
                    Bill(user_id=user_id, name="Electricity", amount=1200, status="UNPAID"),
                    Bill(user_id=user_id, name="Water", amount=450, status="UNPAID"),
                    Bill(user_id=user_id, name="Internet", amount=899, status="UNPAID"),
                    Bill(user_id=user_id, name="Mobile", amount=599, status="UNPAID"),
                    Bill(user_id=user_id, name="Gas", amount=850, status="UNPAID"),
                ]
                db.add_all(bills)
                db.commit()
                print(f"[OK] Created {len(bills)} demo bills")
            else:
                print(f"[INFO] Bills already exist: {existing_bills} unpaid bills")
            
            print()
            print("=" * 60)
            print("[SUCCESS] Database initialization completed successfully!")
            print("=" * 60)
            print()
            print("Demo Account Details:")
            print(f"  Username: chethan")
            print(f"  Password: 1234")
            print(f"  Balance:  Rs.{account.balance}")
            print(f"  Bills:    {existing_bills if existing_bills > 0 else len(bills)} unpaid")
            print()
            print("Next Steps:")
            print("  1. Check Supabase Table Editor to verify tables")
            print("  2. Deploy your application to Vercel")
            print("  3. Test login at /api/v1/auth/login")
            print()
            
        except Exception as e:
            db.rollback()
            print(f"[ERROR] Error seeding data: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
        finally:
            db.close()
            
    except Exception as e:
        print(f"[ERROR] Error creating tables: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
