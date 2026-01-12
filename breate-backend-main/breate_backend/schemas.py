from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# =====================================================
# AUTH & TOKEN SCHEMAS
# =====================================================

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    sub: Optional[str] = None


# =====================================================
# USER SCHEMAS
# =====================================================

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    archetype_id: int
    tier_id: int


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    username: Optional[str]
    bio: Optional[str]
    archetype_id: int
    tier_id: int

    class Config:
        orm_mode = True


# =====================================================
# ARCHETYPE & TIER
# =====================================================

class ArchetypeResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]

    class Config:
        orm_mode = True


class TierResponse(BaseModel):
    id: int
    name: str
    level: int
    description: Optional[str]

    class Config:
        orm_mode = True


# =====================================================
# COALITIONS (IDENTITY ANCHORS)
# =====================================================

class CoalitionBase(BaseModel):
    name: str
    description: Optional[str] = None
    focus: Optional[str] = None
    location: Optional[str] = None


class CoalitionCreate(CoalitionBase):
    pass


class CoalitionMember(BaseModel):
    id: int
    email: EmailStr
    username: Optional[str]

    class Config:
        orm_mode = True


class CoalitionOut(CoalitionBase):
    id: int
    members: List[CoalitionMember] = []

    class Config:
        orm_mode = True


# =====================================================
# PROJECT SCHEMAS
# =====================================================

class ProjectCreate(BaseModel):
    title: str
    objective: str
    project_type: str
    needed_archetypes: List[str]
    open_roles: Optional[str] = None
    timeline: Optional[str] = None
    region: Optional[str] = None
    coalition_tags: Optional[List[str]] = []


class ProjectResponse(BaseModel):
    id: int
    title: str
    objective: str
    project_type: str
    needed_archetypes: List[str]
    open_roles: Optional[str]
    timeline: Optional[str]
    region: Optional[str]
    coalition_tags: List[str]
    status: str
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        orm_mode = True


# =====================================================
# PROJECT PARTICIPATION
# =====================================================

class JoinProjectRequest(BaseModel):
    role: Optional[str] = None


# =====================================================
# COLLABORATION & VERIFICATION
# =====================================================

class VerifyCollaborationRequest(BaseModel):
    contribution_summary: Optional[str] = None


# =====================================================
# COLLAB CIRCLE (READ-ONLY OUTPUT)
# =====================================================

class CollabCircleEntry(BaseModel):
    collaborator_id: int
    collaborator_username: Optional[str]
    project_title: Optional[str]
    verified_at: datetime

    class Config:
        orm_mode = True











