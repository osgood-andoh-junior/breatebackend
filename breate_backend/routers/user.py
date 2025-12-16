from fastapi import APIRouter, HTTPException, Depends, status, Response, Request
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from breate_backend.database import get_db
from breate_backend import models, schemas
from breate_backend.auth import (
    create_access_token,
    create_refresh_token,
    verify_access_token,
    verify_refresh_token
)

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")


# -----------------------------
# Signup Endpoint
# -----------------------------
@router.post("/signup", response_model=schemas.UserResponse)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    Requires: email, password, archetype_id, tier_id.
    """
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = pwd_context.hash(user.password)
    new_user = models.User(
        email=user.email,
        password=hashed_password,
        archetype_id=user.archetype_id,
        tier_id=user.tier_id
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# -----------------------------
# Login Endpoint (Form + Cookies)
# -----------------------------
@router.post("/login", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    response: Response = None,
    db: Session = Depends(get_db)
):
    """
    Authenticates a user and returns access + refresh tokens.
    """
    user = db.query(models.User).filter(models.User.email == form_data.username).first()

    if not user or not pwd_context.verify(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    access_token = create_access_token(data={"sub": user.email, "type": "access"})
    refresh_token = create_refresh_token(data={"sub": user.email, "type": "refresh"})

    if response:
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=False,  # True in production
            samesite="lax"
        )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


# -----------------------------
# Get Current User (/users/me)
# -----------------------------
@router.get("/me", response_model=schemas.UserResponse)
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Returns the current user's information if the access token is valid.
    """
    try:
        payload = verify_access_token(token)
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid access token type")

        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


# -----------------------------
# Refresh Access Token
# -----------------------------
@router.post("/refresh", response_model=schemas.Token)
def refresh_token(request: Request):
    """
    Uses refresh token from cookies to issue a new access token.
    """
    refresh_cookie = request.cookies.get("refresh_token")
    if not refresh_cookie:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    try:
        payload = verify_refresh_token(refresh_cookie)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token type")
        email = payload.get("sub")
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

    new_access_token = create_access_token({"sub": email, "type": "access"})
    return {"access_token": new_access_token, "token_type": "bearer"}
