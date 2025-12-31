from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from breate_backend.database import get_db
from breate_backend import models

router = APIRouter(
    prefix="/discover",
    tags=["Discover"]
)

# =====================================================
# 1️⃣ USER DISCOVERY (Phase 1)
# =====================================================

@router.get("/users")
def discover_users(
    username: Optional[str] = Query(None, description="Search by username"),
    archetype_id: Optional[int] = Query(None),
    tier_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Public endpoint.
    Used by frontend Discover tab to find creators.
    """

    query = db.query(models.User)

    if username:
        query = query.filter(
            models.User.username.ilike(f"%{username}%")
        )

    if archetype_id:
        query = query.filter(
            models.User.archetype_id == archetype_id
        )

    if tier_id:
        query = query.filter(
            models.User.tier_id == tier_id
        )

    users = query.all()

    return [
        {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "bio": user.bio,
            "archetype": user.archetype.name if user.archetype else None,
            "next_build": user.next_build,
        }
        for user in users
    ]


# =====================================================
# 2️⃣ PROJECT DISCOVERY (Phase 1)
# =====================================================

@router.get("/projects")
def discover_projects(
    archetype: Optional[str] = Query(
        None,
        description="Filter by needed archetype (string match)"
    ),
    region: Optional[str] = Query(None),
    coalition: Optional[str] = Query(
        None,
        description="Filter by coalition tag"
    ),
    db: Session = Depends(get_db),
):
    """
    Public endpoint.
    Returns OPEN projects only (Phase 1 rule).
    """

    query = db.query(models.Project)

    # Phase 1: only open projects
    query = query.filter(
        models.Project.status == models.ProjectStatus.open
    )

    if region:
        query = query.filter(
            models.Project.region.ilike(f"%{region}%")
        )

    if archetype:
        query = query.filter(
            models.Project.needed_archetypes.ilike(f"%{archetype}%")
        )

    if coalition:
        query = query.filter(
            models.Project.coalition_tags.ilike(f"%{coalition}%")
        )

    projects = (
        query
        .order_by(models.Project.created_at.desc())
        .all()
    )

    return [
        {
            "id": project.id,
            "title": project.title,
            "objective": project.objective,
            "project_type": project.project_type,
            "needed_archetypes": project.needed_archetypes.split(","),
            "region": project.region,
            "coalition_tags": (
                project.coalition_tags.split(",")
                if project.coalition_tags else []
            ),
            "status": project.status.value,
            "created_at": project.created_at,
            "poster_id": project.poster_id,
        }
        for project in projects
    ]
