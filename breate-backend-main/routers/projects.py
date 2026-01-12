from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from breate_backend.database import get_db
from breate_backend import models
from breate_backend.dependencies.auth_guard import get_current_user

from pydantic import BaseModel


router = APIRouter(
    prefix="/projects",
    tags=["Projects"]
)

# ====================================================
# Schemas
# ====================================================

class ProjectBase(BaseModel):
    title: str
    objective: str
    project_type: str
    needed_archetypes: List[str]

    open_roles: Optional[str] = None
    timeline: Optional[str] = None
    region: Optional[str] = None
    coalition_tags: List[str] = []


class ProjectCreate(ProjectBase):
    pass


class ProjectStatusUpdate(BaseModel):
    status: str  # open | in_progress | completed


class ProjectResponse(ProjectBase):
    id: int
    poster_id: Optional[int]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ====================================================
# Helpers
# ====================================================

VALID_STATUS_FLOW = {
    "open": "in_progress",
    "in_progress": "completed",
}


def validate_status_transition(current: str, new: str):
    if current == "completed":
        raise HTTPException(
            status_code=400,
            detail="Completed projects cannot be updated"
        )

    allowed_next = VALID_STATUS_FLOW.get(current)
    if new != allowed_next:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status transition: {current} → {new}"
        )


# ====================================================
# GET: Public project feed
# ====================================================

@router.get("/", response_model=List[ProjectResponse])
def get_projects(db: Session = Depends(get_db)):
    projects = (
        db.query(models.Project)
        .order_by(models.Project.created_at.desc())
        .all()
    )

    return [
        ProjectResponse(
            id=p.id,
            title=p.title,
            objective=p.objective,
            project_type=p.project_type,
            needed_archetypes=p.needed_archetypes.split(","),
            open_roles=p.open_roles,
            timeline=p.timeline,
            region=p.region,
            coalition_tags=p.coalition_tags.split(",") if p.coalition_tags else [],
            poster_id=p.poster_id,
            status=p.status.value,
            created_at=p.created_at,
        )
        for p in projects
    ]


# ====================================================
# POST: Create project (AUTH REQUIRED)
# ====================================================

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    new_project = models.Project(
        title=project.title,
        objective=project.objective,
        project_type=project.project_type,
        needed_archetypes=",".join(project.needed_archetypes),
        open_roles=project.open_roles,
        timeline=project.timeline,
        region=project.region,
        coalition_tags=",".join(project.coalition_tags),
        poster_id=current_user.id,
    )

    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    return ProjectResponse(
        id=new_project.id,
        title=new_project.title,
        objective=new_project.objective,
        project_type=new_project.project_type,
        needed_archetypes=new_project.needed_archetypes.split(","),
        open_roles=new_project.open_roles,
        timeline=new_project.timeline,
        region=new_project.region,
        coalition_tags=new_project.coalition_tags.split(",") if new_project.coalition_tags else [],
        poster_id=new_project.poster_id,
        status=new_project.status.value,
        created_at=new_project.created_at,
    )


# ====================================================
# GET: Single project
# ====================================================

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(
        models.Project.id == project_id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return ProjectResponse(
        id=project.id,
        title=project.title,
        objective=project.objective,
        project_type=project.project_type,
        needed_archetypes=project.needed_archetypes.split(","),
        open_roles=project.open_roles,
        timeline=project.timeline,
        region=project.region,
        coalition_tags=project.coalition_tags.split(",") if project.coalition_tags else [],
        poster_id=project.poster_id,
        status=project.status.value,
        created_at=project.created_at,
    )


# ====================================================
# PATCH: Update project status (OWNER ONLY)
# ====================================================

@router.patch("/{project_id}/status", response_model=ProjectResponse)
def update_project_status(
    project_id: int,
    payload: ProjectStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    project = db.query(models.Project).filter(
        models.Project.id == project_id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.poster_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to update this project"
        )

    new_status = payload.status

    if new_status not in models.ProjectStatus.__members__:
        raise HTTPException(
            status_code=400,
            detail="Invalid project status"
        )

    current_status = project.status.value
    validate_status_transition(current_status, new_status)

    project.status = models.ProjectStatus[new_status]
    if new_status == "completed":
        project.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(project)

    return ProjectResponse(
        id=project.id,
        title=project.title,
        objective=project.objective,
        project_type=project.project_type,
        needed_archetypes=project.needed_archetypes.split(","),
        open_roles=project.open_roles,
        timeline=project.timeline,
        region=project.region,
        coalition_tags=project.coalition_tags.split(",") if project.coalition_tags else [],
        poster_id=project.poster_id,
        status=project.status.value,
        created_at=project.created_at,
    )


# ====================================================
# DELETE: Project (OWNER ONLY)
# ====================================================

@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    project = db.query(models.Project).filter(
        models.Project.id == project_id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.poster_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to delete this project"
        )

    if project.status != models.ProjectStatus.open:
        raise HTTPException(
            status_code=400,
            detail="Only open projects can be deleted"
        )

    db.delete(project)
    db.commit()

    return {"message": "Project deleted successfully"}



