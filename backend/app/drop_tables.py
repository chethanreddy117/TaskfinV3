# backend/app/drop_tables.py
from app.db import engine, Base
# Import all models to ensure they are registered with Base.metadata
from app.models import User, Account, Bill, Transaction, AuditLog

def drop_all_tables():
    print("⚠️  Warning: This will delete ALL data in the database.")
    confirm = input("Are you sure you want to proceed? (y/N): ")
    
    if confirm.lower() == 'y':
        try:
            print("Dropping all tables...")
            Base.metadata.drop_all(bind=engine)
            print("✅ All tables dropped successfully.")
            print("Next time you start the app, the tables will be recreated with the new schema.")
        except Exception as e:
            print(f"❌ Error dropping tables: {e}")
    else:
        print("Operation cancelled.")

if __name__ == "__main__":
    drop_all_tables()
