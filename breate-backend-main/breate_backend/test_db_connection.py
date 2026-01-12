from breate_backend.database import engine
from sqlalchemy import text

print("🔍 Testing database connection...")

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version();"))
        version = result.scalar()
        print("✅ Connected successfully!")
        print(f"PostgreSQL version: {version}")
except Exception as e:
    print("❌ Connection failed!")
    print(e)
