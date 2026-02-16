#!/usr/bin/env python3
"""
Quick Database Test Script
Tests database connection directly from environment variable
"""
import sys
import os

# Get database URL directly from environment
POSTGRES_URL = os.getenv("POSTGRES_URL")

if not POSTGRES_URL:
    print("[ERROR] POSTGRES_URL environment variable not set!")
    print()
    print("Usage:")
    print('  $env:POSTGRES_URL = "your-connection-string"')
    print("  python test_db_connection.py")
    sys.exit(1)

# Convert postgres:// to postgresql:// if needed
DATABASE_URL = POSTGRES_URL
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Obfuscate password for display
db_url_display = DATABASE_URL
if "@" in db_url_display:
    parts = db_url_display.split("@")
    credentials = parts[0].split("://")[1]
    if ":" in credentials:
        user = credentials.split(":")[0]
        db_url_display = db_url_display.replace(credentials, f"{user}:****")

print("=" * 60)
print("Database Connection Test")
print("=" * 60)
print(f"[DB] Connection URL: {db_url_display}")
print()

# Try to connect
try:
    from sqlalchemy import create_engine, inspect, text
    
    print("[*] Creating database engine...")
    engine = create_engine(DATABASE_URL)
    
    print("[*] Testing connection...")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.scalar()
        print(f"[OK] Connected successfully!")
        print(f"[INFO] PostgreSQL version: {version[:50]}...")
    
    print()
    print("[*] Checking existing tables...")
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    if tables:
        print(f"[INFO] Found {len(tables)} tables: {', '.join(tables)}")
    else:
        print("[INFO] No tables found in database (fresh database)")
    
    print()
    print("=" * 60)
    print("[SUCCESS] Database connection test passed!")
    print("=" * 60)
    print()
    print("Next step: Run init_db.py to create tables")
    
except Exception as e:
    print(f"[ERROR] Connection failed: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
