import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# -------------------------------------------------
# Load environment variables (.env at project root)
# -------------------------------------------------
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# -------------------------------------------------
# Database URL
# -------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is missing. Check your .env file at the project root."
    )

# -------------------------------------------------
# Engine (Neon Postgres)
# -------------------------------------------------
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,     # handles dropped connections
    pool_size=5,
    max_overflow=10,
    echo=False
)

# -------------------------------------------------
# Session
# -------------------------------------------------
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# -------------------------------------------------
# Base
# -------------------------------------------------
Base = declarative_base()

# -------------------------------------------------
# Dependency
# -------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

