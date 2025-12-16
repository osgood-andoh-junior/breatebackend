from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from breate_backend.database import get_db
from breate_backend import models
from breate_backend.dependencies.auth_guard import get_current_user
from pydantic import BaseModel

router = APIRouter(
    prefix="/collabcircle",
    tags=["Collab Circle"]
)

# =====================================================
# Schemas
# =====================================================

class CollabCreate(BaseModel):
    collaborator_username: str
    project_name: Optional[str] = None


class CollabResponse(BaseModel):
    id: int
    user_a_username: str
    user_b_username: str
    project_name: Optional[str]
    status: str
    created_at: datetime
    verified_at: Optional[datetime]

    class Config:
        from_attributes = True


# =====================================================
# CREATE COLLAB LINK (MANUAL – PHASE 1)
# =====================================================

@router.post("/", response_model=CollabResponse, status_code=status.HTTP_201_CREATED)
def create_collaboration(
    payload: CollabCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    collaborator = (
        db.query(models.User)
        .filter(models.User.username == payload.collaborator_username)
        .first()
    )

    if not collaborator:
        raise HTTPException(status_code=404, detail="User not found")

    if collaborator.username == current_user.username:
        raise HTTPException(status_code=400, detail="Cannot collaborate with yourself")

    # Prevent duplicate collaborations
    existing = (
        db.query(models.CollabLink)
        .filter(
            (
                (models.CollabLink.user_a_username == current_user.username) &
                (models.CollabLink.user_b_username == collaborator.username)
            ) |
            (
                (models.CollabLink.user_a_username == collaborator.username) &
                (models.CollabLink.user_b_username == current_user.username)
            )
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Collaboration already exists"
        )

    collab = models.CollabLink(
        user_a_username=current_user.username,
        user_b_username=collaborator.username,
        project_name=payload.project_name,
        status="pending",
        user_a_confirmed=1,
        user_b_confirmed=0,
    )

    db.add(collab)
    db.commit()
    db.refresh(collab)

    return collab


# =====================================================
# GET MY COLLABORATIONS
# =====================================================

@router.get("/me", response_model=List[CollabResponse])
def get_my_collaborations(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    collabs = (
        db.query(models.CollabLink)
        .filter(
            (models.CollabLink.user_a_username == current_user.username) |
            (models.CollabLink.user_b_username == current_user.username)
        )
        .order_by(models.CollabLink.created_at.desc())
        .all()
    )

    return collabs





