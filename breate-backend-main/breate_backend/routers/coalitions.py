from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from breate_backend.database import get_db
from breate_backend import models

router = APIRouter(
    prefix="/coalitions",
    tags=["Coalitions"]
)

# =====================================================
# GET: All coalitions (Phase 1)
# =====================================================

@router.get("/")
def get_coalitions(
    search: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Public endpoint.
    Used for Coalitions tab.
    """

    query = db.query(models.Coalition)

    if search:
        s = f"%{search}%"
        query = query.filter(
            (models.Coalition.name.ilike(s)) |
            (models.Coalition.focus.ilike(s)) |
            (models.Coalition.location.ilike(s))
        )

    if region:
        query = query.filter(models.Coalition.location.ilike(f"%{region}%"))

    coalitions = (
        query
        .order_by(models.Coalition.created_at.desc())
        .all()
    )

    return [
        {
            "id": c.id,
            "name": c.name,
            "description": c.description,
            "focus": c.focus,
            "location": c.location,
            "member_count": len(c.members),
            "created_at": c.created_at,
        }
        for c in coalitions
    ]


# =====================================================
# GET: Single coalition + members (Phase 1)
# =====================================================

@router.get("/{coalition_id}")
def get_coalition(coalition_id: int, db: Session = Depends(get_db)):
    """
    Public endpoint.
    Coalition detail page.
    """

    coalition = (
        db.query(models.Coalition)
        .filter(models.Coalition.id == coalition_id)
        .first()
    )

    if not coalition:
        raise HTTPException(status_code=404, detail="Coalition not found")

    return {
        "id": coalition.id,
        "name": coalition.name,
        "description": coalition.description,
        "focus": coalition.focus,
        "location": coalition.location,
        "created_at": coalition.created_at,
        "members": [
            {
                "id": u.id,
                "username": u.username,
                "bio": u.bio,
                "archetype": u.archetype.name if u.archetype else None,
                "tier": u.tier.name if u.tier else None,
            }
            for u in coalition.members
        ],
    }













