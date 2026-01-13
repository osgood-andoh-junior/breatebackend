from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from breate_backend.database import get_db
from breate_backend import models, schemas

router = APIRouter(
    prefix="/tiers",
    tags=["Tiers"]
)

# -----------------------------
# Get All Tiers
# -----------------------------
@router.get("/", response_model=list[schemas.TierResponse])
def get_tiers(db: Session = Depends(get_db)):
    """
    Returns all available tiers.
    """
    tiers = db.query(models.Tier).all()
    # Return empty array instead of 404 if no tiers found
    return tiers or []
