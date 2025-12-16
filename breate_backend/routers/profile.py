from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from breate_backend.database import get_db
from breate_backend import models
from breate_backend.dependencies.auth_guard import get_current_user

router = APIRouter(
    prefix="/profile",
    tags=["Profile"]
)

# ----------------------------------------------------
# GET: Public user profile
# ----------------------------------------------------
@router.get("/{username}")
def get_profile(
    username: str,
    db: Session = Depends(get_db),
):
    user = (
        db.query(models.User)
        .filter(models.User.username == username)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "bio": user.bio,
        "preferred_themes": user.preferred_themes,
        "portfolio_links": user.portfolio_links,
        "next_build": user.next_build,
        "affiliations": user.affiliations,
        "archetype": user.archetype.name if user.archetype else None,
        "tier": user.tier.name if user.tier else None,
    }


# ----------------------------------------------------
# PUT: Update own profile (OWNER ONLY)
# ----------------------------------------------------
@router.put("/{username}")
def update_profile(
    username: str,
    data: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.username != username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to edit this profile"
        )

    user = (
        db.query(models.User)
        .filter(models.User.id == current_user.id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    allowed_fields = {
        "full_name",
        "bio",
        "preferred_themes",
        "portfolio_links",
        "next_build",
        "affiliations",
    }

    for field in allowed_fields:
        if field in data:
            setattr(user, field, data[field])

    db.commit()
    db.refresh(user)

    return {
        "message": "Profile updated successfully"
    }



