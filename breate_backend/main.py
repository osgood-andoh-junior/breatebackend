import os

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
import logging

from breate_backend.database import engine, get_db, SessionLocal
from breate_backend import models

# -------------------------------------------------
# Import routers
# -------------------------------------------------
from breate_backend.routers import (
    # auth,  # Not used - frontend uses /users/* endpoints instead
    user,
    profile,
    archetype,
    tier,
    discover,
    projects,
    coalitions,
    collabcircle,
)

# -------------------------------------------------
# App
# -------------------------------------------------
app = FastAPI(
    title="Breate API",
    version="1.0.0",
    description="Backend API for the Breate Web App (Phase 1 MVP)",
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    origin = request.headers.get('origin', 'N/A')
    method = request.method
    path = request.url.path
    query = str(request.url.query) if request.url.query else ""
    full_path = f"{path}?{query}" if query else path
    
    logger.info(f"📥 {method} {full_path}")
    logger.info(f"   Origin: {origin}")
    logger.info(f"   Headers: {dict(request.headers)}")
    
    response = await call_next(request)
    
    logger.info(f"📤 {method} {full_path} - Status: {response.status_code}")
    if response.status_code >= 400:
        logger.error(f"   ❌ Error response: {response.status_code}")
    
    return response

# -------------------------------------------------
# CORS (Dev + Prod Safe)
# -------------------------------------------------
# Set this in production:
# CORS_ORIGINS=https://your-frontend.vercel.app,https://your-frontend-git-main.vercel.app
#
# Local default:
# http://localhost:3000,http://127.0.0.1:3000

# Parse CORS origins - strip whitespace and filter empty strings
cors_origins_str = os.getenv(
    "CORS_ORIGINS",
    "*"  # Default to allow all origins for debugging (change in production)
)

# If CORS_ORIGINS is "*", allow all origins, otherwise parse the list
if cors_origins_str.strip() == "*":
    cors_origins = ["*"]
    logger.warning("⚠️  CORS set to allow all origins (*) - not recommended for production!")
else:
    cors_origins = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]
    logger.info(f"🌐 CORS Origins configured: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
    expose_headers=["Content-Type", "Authorization"],
)

# -------------------------------------------------
# Database bootstrap (Phase 1 only)
# -------------------------------------------------
print("🛠️ Initializing database schema...")
models.Base.metadata.create_all(bind=engine)
print("✅ Database schema ready.")

# -------------------------------------------------
# Routers
# -------------------------------------------------
API_PREFIX = "/api/v1"

# Note: auth.router contains /auth/register and /auth/login which are NOT used
# Frontend uses /users/signup and /users/login instead
# Keeping auth router commented out to avoid confusion
# app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(user.router, prefix=API_PREFIX)
app.include_router(profile.router, prefix=API_PREFIX)
app.include_router(archetype.router, prefix=API_PREFIX)
app.include_router(tier.router, prefix=API_PREFIX)
app.include_router(discover.router, prefix=API_PREFIX)
app.include_router(projects.router, prefix=API_PREFIX)
app.include_router(coalitions.router, prefix=API_PREFIX)
app.include_router(collabcircle.router, prefix=API_PREFIX)

# -------------------------------------------------
# Root
# -------------------------------------------------
@app.get("/", tags=["Root"])
def root():
    return {"message": "Welcome to the Breate API (Phase 1 MVP)"}

# -------------------------------------------------
# Health checks
# -------------------------------------------------
@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "api_version": "1.0.0",
        "endpoints": {
            "archetypes": "/api/v1/archetypes/",
            "tiers": "/api/v1/tiers/",
            "login": "/api/v1/users/login",
            "signup": "/api/v1/users/signup"
        }
    }

@app.get("/health/db", tags=["Health"])
def check_db_connection(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT version();"))
        return {
            "status": "connected",
            "postgres_version": result.scalar()
        }
    except Exception as e:
        return {
            "status": "error",
            "detail": str(e)
        }

# -------------------------------------------------
# Seed core reference data (idempotent)
# -------------------------------------------------
@app.on_event("startup")
def seed_reference_data():
    db = SessionLocal()
    try:
        # Archetypes
        archetypes = [
            ("Creator", "Visionary builders who bring ideas to life."),
            ("Creative", "Expressive individuals skilled in storytelling and design."),
            ("Innovator", "Thinkers who challenge norms and create new approaches."),
            ("Systems Thinker", "Analytical minds who design scalable systems."),
        ]

        for name, description in archetypes:
            if not db.query(models.Archetype).filter_by(name=name).first():
                db.add(models.Archetype(name=name, description=description))

        # Tiers
        tiers = [
            ("Base", 1, "Entry-level creators starting out."),
            ("Standard", 2, "Intermediate users gaining experience."),
            ("Professional", 3, "Experts with consistent contributions."),
        ]

        for name, level, description in tiers:
            if not db.query(models.Tier).filter_by(name=name).first():
                db.add(models.Tier(name=name, level=level, description=description))

        # Coalitions
        coalitions = [
            ("University of Ghana", "Academic creative ecosystem", "Education", "Ghana"),
            ("Tech for Good", "Builders using tech for social impact", "Innovation", "Africa"),
        ]

        for name, description, focus, location in coalitions:
            if not db.query(models.Coalition).filter_by(name=name).first():
                db.add(
                    models.Coalition(
                        name=name,
                        description=description,
                        focus=focus,
                        location=location,
                    )
                )

        db.commit()
        print("✅ Reference data seeded")

    except Exception as e:
        print("❌ Error seeding reference data:", str(e))
    finally:
        db.close()



